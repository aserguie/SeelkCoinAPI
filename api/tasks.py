from __future__ import absolute_import, unicode_literals
import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from smtplib import SMTPException
from celery import shared_task
from .celery import app
from alert.models import Alert
from api.settings import BASE_URL, DEFAULT_FROM_EMAIL

RATE_VALUES = {}


def get_alert_message(alert):
    """Customizes the content fof the email sent to the user"""
    msg = (
        f"Hello {alert.user.username}, the exchange rate of "
        f"{alert.base_currency}/{alert.quote_currency} has "
    )
    if alert.period:
        msg += (
            f"moved more than {alert.evolution_rate}% in less than "
            f"{alert.period}(S)."
        )
    else:
        msg += f"met a threshold of {alert.threshold} moving "
        if alert.is_upper_bound:
            msg += "upwards."
        else:
            msg += "downwards."
    return msg


@app.task(bind=True, default_retry_delay=10 * 60)
def send_email_alert(self, alert_id):
    """
    Sends an email to user letting him know one of his alerts
    just met his criteria and retries every 10 minutes in case
    if fails.
    """
    alert = Alert.objects.get(id=alert_id)
    try:
        context = {
            "title": f"New alert:{alert.base_currency}/{alert.quote_currency}",
            "text": get_alert_message(alert),
        }
        message = render_to_string("template.txt", context)
        html_message = render_to_string("template_inline.html", context)
        send_mail(
            subject="New alert",
            message=message,
            from_email=DEFAULT_FROM_EMAIL,
            recipient_list=[alert.user.email],
            fail_silently=False,
            html_message=html_message,
        )
    except SMTPException as ex:
        self.retry(exc=ex)


def get_starting_rate(validated_data):
    """ Returns the rate on alert creation"""
    return (
        RATE_VALUES[validated_data["base_currency"]]
        / RATE_VALUES[validated_data["quote_currency"]]
    )


def update_rate_values(base_currency, quote_currency, response):
    """ Stores the rates of every active alert currency"""
    for asset in response.json():
        if asset["asset_id"] in [base_currency, quote_currency]:
            RATE_VALUES[asset["asset_id"]] = asset["price_usd"]


def threshold_is_met(alert):
    """
    Returns True if an exchange rate met its defined threshold or evolved more
    than the provided evolution rate within a rolling window of length period.
    Else, in case of a period-type alert, the period_start attribute of alert
    is incremented
    """
    base_quote_rate = (
        RATE_VALUES[alert.base_currency] / RATE_VALUES[alert.quote_currency]
    )
    if alert.is_upper_bound:
        if (
            alert.period
            and timezone.now() < alert.period_start + alert.period
            and base_quote_rate
            > alert.starting_value_in_quote * (1 + (alert.evolution_rate / 100))
        ):
            return True
        if not alert.period and base_quote_rate > alert.threshold:
            return True
    else:
        if (
            alert.period
            and timezone.now() < alert.period_start + alert.period
            and base_quote_rate
            <= alert.starting_value_in_quote * (1 + (alert.evolution_rate / 100))
        ):
            return True
        if not alert.period and base_quote_rate < alert.threshold:
            return True
    if alert.period and timezone.now() >= alert.period_start + alert.period:
        alert.period_start = timezone.now()
        alert.starting_value_in_quote = (
            RATE_VALUES[alert.base_currency] / RATE_VALUES[alert.quote_currency]
        )
    alert.save()
    return False


@shared_task
def check_prices(alert_id):
    """Task attached to an alert object that frequently checks
    if the exchange rate hasn't met its boundary
    """
    if Alert.objects.filter(id=alert_id, is_active=True):
        alert = Alert.objects.get(id=alert_id)
        update_prices(alert.base_currency, alert.quote_currency)
        if threshold_is_met(alert):
            send_email_alert.apply_async((alert.id,))
            alert.is_active = False
            alert.save()
        else:
            if alert.period:
                check_prices.apply_async(
                    (alert_id,), countdown=alert.period.total_seconds()
                )
            else:
                check_prices.apply_async((alert_id,), countdown=60)


def update_prices(base_currency, quote_currency):
    response = requests.get(url=BASE_URL + "assets")
    try:
        response.raise_for_status()
        update_rate_values(base_currency, quote_currency, response)
    except requests.exceptions.RequestException as e:
        return e


@shared_task
def relaunch_tasks():
    """
    Task that reactivates tasks for every alert, in case the server went down
    (or in development environment)
    """
    for alert in Alert.objects.filter(is_active=True):
        check_prices.apply_async((alert.id,), concurrency=1)


relaunch_tasks.apply_async(concurrency=1)
