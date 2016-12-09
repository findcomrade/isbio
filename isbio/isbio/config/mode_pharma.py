from isbio.config.CAS import *
from isbio.settings import PH_DOMAINS
from isbio.config.new_sge import *

TEMPLATE_DEBUG = False
DEBUG = False
SHINY_MODE = 'remote'
SHINY_LOCAL_ENABLE = False

ALLOWED_HOSTS = PH_DOMAINS + [CAS_SERVER_IP]
BREEZE_TITLE = 'BREEZE-N-PH'
BREEZE_TITLE_LONG = 'Breeze new-Pharma'

# contains everything else (including breeze generated content) than the breeze web source code and static files
PROJECT_FOLDER_NAME = 'projects'
# PROJECT_FOLDER_PREFIX = '/fs'
PROJECT_FOLDER_PREFIX = '/fs'
PROJECT_FOLDER = '%s/%s/' % (PROJECT_FOLDER_PREFIX, PROJECT_FOLDER_NAME)
BREEZE_PROD_FOLDER = 'breeze'
BREEZE_PHARMA_FOLDER = '%s-ph2' % BREEZE_PROD_FOLDER
BREEZE_FOLDER = '%s/' % BREEZE_PHARMA_FOLDER
