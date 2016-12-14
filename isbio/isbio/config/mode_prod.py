from isbio.config.auth0 import *
from azure_cloud import *

TEMPLATE_DEBUG = False
DEBUG = False
SHINY_MODE = 'remote'
SHINY_LOCAL_ENABLE = False
BREEZE_TITLE = 'C-BREEZE'
BREEZE_TITLE_LONG = 'Cloud Breeze'

# contains everything else (including breeze generated content) than the breeze web source code and static files
PROJECT_FOLDER_NAME = 'projects'
# PROJECT_FOLDER_PREFIX = '/fs'
PROJECT_FOLDER_PREFIX = ''
PROJECT_FOLDER = '%s/%s/' % (PROJECT_FOLDER_PREFIX, PROJECT_FOLDER_NAME)
BREEZE_PROD_FOLDER = 'breeze'
BREEZE_FOLDER = '%s/' % BREEZE_PROD_FOLDER
