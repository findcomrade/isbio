from isbio.config.execution.docker import * # !important, do not delete
from isbio.settings import SOURCE_ROOT, DomainList
from isbio.config import DEV_MODE
DOMAIN = DomainList.CLOUD_DEV if DEV_MODE else DomainList.CLOUD_PROD
from auth.auth0 import *
ALLOWED_HOSTS = DOMAIN + AUTH0_IP_LIST

# might go into docker config ?
DOCKER_HUB_PASS_FILE = SOURCE_ROOT + 'docker_repo'
AZURE_PASS_FILE = SOURCE_ROOT + 'azure_pwd'
# override Shiny mode (may be on if run mode is dev)
SHINY_MODE = 'remote'
SHINY_LOCAL_ENABLE = False
BREEZE_TITLE = 'C-BREEZE' + ('-DEV' if DEV_MODE else '')
BREEZE_TITLE_LONG = 'Cloud Breeze' + (' (dev)' if DEV_MODE else '')

STATICFILES_DIRS = (
	# Put strings here, like "/home/html/static" or "C:/www/django/static".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	"/root/static_source",
)
