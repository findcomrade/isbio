from breeze.utilities import *
from django.conf import settings
from settings import *
# Django settings for isbio project.
# from configurations import Settings

API_VERSION = '1.0'

GIT_PULL_MASTER = 'git pull origin master'
GIT_PULL_DEV = 'git pull origin dev'

API_PULL_COMMAND = GIT_PULL_DEV if settings.DEV_MODE else GIT_PULL_MASTER
