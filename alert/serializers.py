from rest_framework import serializers
from datetime import timedelta
from api.tasks import check_prices, update_rate_values, get_starting_rate
from user.models import User
from .models import Alert, ASSET_LIST


class AlertSerializer(serializers.ModelSerializer):
    """
    On creation a base currency has to be sent, the quote currency is
    set by default to USD but both base and quote currencies can be changed.
    The user must provide either a max/min threshold for his eschange rate
    or an evolution percentage goal and a corresponding period.
    """

    base_currency = serializers.CharField(max_length=10)
    quote_currency = serializers.CharField(max_length=10, default="USD")
    threshold = serializers.DecimalField(
        max_digits=38, decimal_places=9, required=False
    )
    evolution_rate = serializers.DecimalField(
        max_digits=38, decimal_places=9, required=False
    )
    period = serializers.DurationField(required=False)

    class Meta:
        model = Alert
        fields = "__all__"
        read_only_fields = ["id", "created", "user"]

    def create(self, validated_data, response):
        """
        The user attached to the alert is grabbed from the route used to create it
        Regular users can only access their alerts on /alerts route whereas a
        staff member can access to any alert on /users/<pk>/alerts though it is
        forbidden even for him to change the alert's user to another user
        """
        view = self.context["view"]
        request = self.context["request"]
        if "user" in view.kwargs:
            user = User.objects.get(id=view.kwargs["user"])
        else:
            user = request.user
        if "quote_currency" not in validated_data:
            validated_data["quote_currency"] = "USD"
        update_rate_values(
            validated_data["base_currency"], validated_data["quote_currency"], response
        )
        validated_data["starting_value_in_quote"] = get_starting_rate(validated_data)
        alert = Alert.objects.create(user=user, **validated_data)
        check_prices.apply_async((alert.id,))
        alert.save()
        return alert

    def update(self, instance, validated_data, response):
        update_rate_values(
            validated_data["base_currency"], validated_data["quote_currency"], response
        )
        validated_data["starting_value_in_quote"] = get_starting_rate(validated_data)
        if instance.is_active is False:
            check_prices.apply_async((instance.id,))
        instance.is_active = True
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def validate_base_currency(self, value):
        if value not in ASSET_LIST:
            raise serializers.ValidationError(
                "This base currency is not supported, you must pick one from "
                + f"the following list: {ASSET_LIST}"
            )
        return value

    def validate_quote_currency(self, value):
        if value not in ASSET_LIST:
            raise serializers.ValidationError(
                "This quote currency is not supported, you must pick one from "
                + f"the following list: {ASSET_LIST}"
            )
        return value

    def validate_threshold(self, value):
        if value < 0:
            raise serializers.ValidationError(
                "The threshold has to be a positive number"
            )
        return value

    def validate_evolution_rate(self, value):
        if value < -100:
            raise serializers.ValidationError(
                "The evolution rate cannot be lower than -100%"
            )
        if value == 0:
            raise serializers.ValidationError("The evolution rate cannot be null")
        return value

    def validate_period(self, value):
        if value <= timedelta(0):
            raise serializers.ValidationError(
                "This period is not supported, you must provide a positive "
                + "duration expressed in seconds"
            )
        return value

    def validate(self, data):
        """
        This function performs some cross validation between parameters to
        avoid clashing values
        """
        if not self.instance:
            if "threshold" in data and ("evolution_rate" in data or "period" in data):
                raise serializers.ValidationError(
                    "You must provide either a threshold for your alert "
                    + "or an evolution rate/period couple but not both at once"
                )
            if "threshold" not in data and "evolution_rate" not in data:
                raise serializers.ValidationError(
                    "You must provide at least a threshold or an evolution "
                    + "rate/period couple for your alert"
                )
            if ("evolution_rate" in data and "period" not in data) or (
                "evolution_rate" not in data and "period" in data
            ):
                raise serializers.ValidationError(
                    "You must provide both an evolution rate and a period for "
                    + "your alert"
                )
        else:
            base_currency = self.instance.base_currency
            quote_currency = self.instance.quote_currency
            if (
                self.instance.threshold
                and ("evolution_rate" in data or "period" in data)
            ) or (self.instance.period and ("threshold" in data)):
                raise serializers.ValidationError(
                    "You cannot change type of alert from a threshold alert "
                    + "to an evolution rate/period alert or vice-versa"
                )
        if "base_currency" in data:
            target_base_currency = data["base_currency"]
        else:
            target_base_currency = base_currency
        if "quote_currency" in data:
            target_quote_currency = data["quote_currency"]
        else:
            target_quote_currency = quote_currency
        if target_base_currency == target_quote_currency:
            raise serializers.ValidationError(
                "Base currency and quote currency must be different."
                + "By default, quote currency is set to USD"
            )
        return data
