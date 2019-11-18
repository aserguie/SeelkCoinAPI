from django.conf import settings
from django.db import models
from api.settings import BASE_URL, HEADERS
import requests


def get_asset_list():
    """
    This function returns the list of all assets where a USD exchange rate
    is provided by the coinapi.io API
    The user can pick any two currencies from this list to create his alerts
    """
    asset_list = []
    response = requests.get(url=BASE_URL + "assets", headers=HEADERS)
    try:
        response.raise_for_status()
        for asset in response.json():
            if "price_usd" in asset:
                asset_list.append(asset["asset_id"])
    except requests.exceptions.HTTPError as e:
        raise e
    return asset_list


ASSET_LIST = get_asset_list()


class Alert(models.Model):
    """
    Alert model containing base and quote currencies
    and either a threshold that has to be met or an evolution
    rate matched with a rolling period
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts"
    )
    created = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField(auto_now=True)
    base_currency = models.CharField(max_length=10)
    quote_currency = models.CharField(max_length=10)
    threshold = models.DecimalField(
        max_digits=38, decimal_places=9, null=True, blank=True
    )
    evolution_rate = models.DecimalField(
        max_digits=38, decimal_places=9, null=True, blank=True
    )
    period = models.DurationField(null=True, blank=True)
    starting_value_in_quote = models.DecimalField(
        max_digits=38, decimal_places=9, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("created",)

    def __str__(self):
        if self.threshold:
            content = (
                f"{self.user.username}: {self.base_currency}/{self.quote_currency} "
                f"{self.starting_value_in_quote} "
                f"meets {self.threshold}"
            )
        else:
            content = (
                f"{self.user.username}: {self.base_currency}/{self.quote_currency} "
                f"{self.starting_value_in_quote} "
                f"gains/loses {self.evolution_rate}% in {self.period}"
            )
        return content

    @property
    def is_upper_bound(self):
        """
        This method returns a Boolean value that informs on the waited trend
        of the alert (upwards/downwards)
        """
        if self.evolution_rate and self.evolution_rate >= 0:
            return True
        if self.threshold and self.threshold >= self.starting_value_in_quote:
            return True
        return False
