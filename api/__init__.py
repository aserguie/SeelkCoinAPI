# This ensures that the app is loaded when Django starts

from .celery import app as celery_app

__all__ = ["celery_app"]
