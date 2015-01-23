"""
Celery config for {{ project_name }} project.
"""

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{ project_name }}.settings")

from sellmo import params
from sellmo.celery.integration import app

params.worker_mode = True
