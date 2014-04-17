"""
Celery config for {{ project_name }} project.
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

# !! This will boot sellmo
from sellmo.boot.celery import app