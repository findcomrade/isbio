from isbio.config.CAS import *
from isbio.settings import PH_DOMAINS
from isbio.config.new_sge import *

TEMPLATE_DEBUG = False
DEBUG = False
SHINY_MODE = 'remote'
SHINY_LOCAL_ENABLE = False

ALLOWED_HOSTS = PH_DOMAINS + [CAS_SERVER_IP]
