"""
	Clem 15/12/2016
	
	This package provide and interface for multi-level configuration :
	_ run mode : PROD, DEV, PHARMA, ...
	_ run environment : FIMM, Azure_Cloud, ...
	_ execution system configurations : docker, sge, ... (TODO moved this to future exec modules setting class)
	_ auth backends : auth0, CAS, ...
	
	This module provide tools for the automatic configuration to happen
	Breeze settings depends on two files :
	MODE_FILE and ENV_FILE which defines respectively the RUN_MODE and the RUN_ENV modules to load
	(the path to these two file has to be defined there-after, and each file has to contain the name of the associated
	python module)
	Those modules then chain all other settings modules :
		_ mode/* shall only contain configuration relevant to the run mode,
		_ while env/* will import the desired auth/* and exec/* configuration modules
	
"""
from isbio.settings import SOURCE_ROOT
from utilz import file_content # , magic_const, MagicAutoConstEnum, magic_const_object_from_list
from django.core.exceptions import ImproperlyConfigured
import mode
import execution
import env
import env.auth


class BreezeImproperlyConfigured(ImproperlyConfigured):
	pass


def auto_conf_from_file(a_name, file_name, object_enum):
	""" check the content of a var file (which shall be one of named object_enum) and return the content if valid """
	file_path = SOURCE_ROOT + file_name
	content = file_content(file_path)
	if not content:
		raise BreezeImproperlyConfigured('%s not specified in %s or file not found' % (a_name, file_path))
	if content not in object_enum:
		raise BreezeImproperlyConfigured('%s not listed in ConfigRunModesList' % a_name)
	return content


def check_defined_filled(*args):
	for each in args:
		if each not in globals() or not globals().get(each, None):
			raise ImproperlyConfigured('%s is not defined, or not filled.' % each)
	return True

# Static object describing available Auth Backends
ConfigAuthMethods = env.auth.config_list # ConfigAuthMethodsList()

# Static object describing available Environments
ConfigEnvironments = env.config_list # ConfigEnvironmentsList()

# Static object describing available Executions backends
ConfigExec = execution.config_list # ConfigExecList()

# Static object describing available Run Modes
ConfigRunModes = mode.config_list # ConfigRunModesList()


#################################
#  CONFIGURES RUN MODE SETTINGS #
#################################
RUN_MODE = auto_conf_from_file('Run mode', '.run_mode', ConfigRunModes)
DEV_MODE = RUN_MODE == 'dev'
PHARMA_MODE = RUN_MODE == 'pharma'
MODE_PROD = RUN_MODE == 'prod'
#########################################
#  CONFIGURES RUN ENVIRONEMENT SETTINGS #
#########################################
RUN_ENV = auto_conf_from_file('Run env', '.run_env', ConfigEnvironments)

# TODO
# ## NOW import everything

AUTH_BACKEND = ConfigAuthMethods.undefined
# Commons
PROJECT_FOLDER_NAME = 'projects'
BREEZE_PROD_FOLDER = 'breeze'

# checks
check_defined_filled('TEMPLATE_FOLDER', 'SOURCE_ROOT')

# run mode first

if MODE_PROD:
	from mode.prod import *
	RUN_MODE_CLASS = ConfigRunModes.prod
elif PHARMA_MODE:
	from mode.pharma import *
	RUN_MODE_CLASS = ConfigRunModes.pharma
elif DEV_MODE:
	from mode.dev import *
	RUN_MODE_CLASS = ConfigRunModes.dev

check_defined_filled('PROJECT_FOLDER_PREFIX', 'PROJECT_FOLDER_NAME', 'ENABLE_NOTEBOOK')
PROJECT_FOLDER = '%s/%s/' % (PROJECT_FOLDER_PREFIX, PROJECT_FOLDER_NAME)
# then environement

if RUN_ENV == 'AzureCloud':
	from env.azure_cloud import *
	RUN_ENV_CLASS = ConfigEnvironments.AzureCloud
elif RUN_ENV == 'FIMM':
	from env.FIMM import *
	RUN_ENV_CLASS = ConfigEnvironments.FIMM

check_defined_filled('BREEZE_FOLDER', 'PROJECT_FOLDER_NAME', 'ALLOWED_HOSTS', 'BREEZE_TITLE', 'BREEZE_TITLE_LONG',
	'AUTHENTICATION_BACKENDS', 'STATICFILES_DIRS')

