from breeze.utilities import *
from django.conf import settings as settings
# from isbio.settings import *
# Django settings for isbio project.
# from configurations import Settings

# override default 404
settings.handler404 = 'api.common.handler404'


API_VERSION = '1.0'

GIT_PULL_MASTER = 'git pull origin master'
GIT_PULL_DEV = 'git pull origin dev'

API_PULL_COMMAND = GIT_PULL_DEV if settings.DEV_MODE else GIT_PULL_MASTER
