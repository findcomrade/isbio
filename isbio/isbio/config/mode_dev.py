from isbio.config.auth0 import *
from azure_cloud import *

TEMPLATE_DEBUG = True
DEBUG = True
SHINY_MODE = 'local'
SHINY_LOCAL_ENABLE = True
BREEZE_TITLE = 'C-BREEZE-DEV'
BREEZE_TITLE_LONG = 'Cloud Breeze (dev)'

# contains everything else (including breeze generated content) than the breeze web source code and static files
PROJECT_FOLDER_NAME = 'projects'
# PROJECT_FOLDER_PREFIX = '/fs'
PROJECT_FOLDER_PREFIX = ''
PROJECT_FOLDER = '%s/%s/' % (PROJECT_FOLDER_PREFIX, PROJECT_FOLDER_NAME)
BREEZE_PROD_FOLDER = 'breeze'
BREEZE_DEV_FOLDER = '%s-dev' % BREEZE_PROD_FOLDER
BREEZE_FOLDER = '%s/' % BREEZE_DEV_FOLDER
