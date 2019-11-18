from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create(self, email, username, password, **extra_fields):
        if not username:
            raise ValueError("The username must be set")
        if not email:
            raise ValueError("The email address must be set")
        user = self.model(
            email=self.normalize_email(email), username=username, **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create(
            email=email, username=username, password=password, **extra_fields
        )

    def create_superuser(self, email, username, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create(
            email=email, username=username, password=password, **extra_fields
        )


class User(AbstractUser):
    objects = UserManager()
    email = models.EmailField(max_length=60)
    username = models.CharField(max_length=30, unique=True)
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    """
    This function generates and saves a token whenever a user is
    created or when he logs in
    """
    if created:
        Token.objects.create(user=instance)
