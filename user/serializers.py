from rest_framework import serializers
from user.models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Quite generic user serializer, the only added thing is
    the confirm_password field that requires the user to enter
    his password twice and both passwords to match before account creation
    """

    confirm_password = serializers.CharField(
        style={"input_type": "password"}, write_only=True
    )

    class Meta:
        model = User
        fields = ["id", "email", "username", "password", "confirm_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        email = validated_data["email"]
        username = validated_data["username"]
        password = validated_data["password"]
        confirm_password = validated_data["confirm_password"]
        if password != confirm_password:
            raise serializers.ValidationError({"password": "Passwords must match"})
        user = User.objects.create_user(email=email, username=username)
        user.set_password(password)
        user.save()
        return user
