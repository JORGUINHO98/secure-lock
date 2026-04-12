"""Celery configuration for Secure Lock."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secure_lock.settings")

app = Celery("secure_lock")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
