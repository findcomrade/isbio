from . import settings
from breeze.utilities import *
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import SuspiciousOperation
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import time
import json

CT_JSON = 'application/json'
CT_TEXT = 'text/plain'
empty_dict = dict()

HTTP_SUCCESS = 200
HTTP_FAILED = 400
HTTP_NOT_FOUND = 404
CUSTOM_MSG = {
	HTTP_SUCCESS: 'ok',
	HTTP_FAILED: 'error',
	HTTP_NOT_FOUND: 'NOT FOUND',
}


# clem 18/10/2016
def get_response(result=True, data=empty_dict, version=settings.API_VERSION):
	return get_response_opt(data, make_http_code(result), version, make_message(result))
	

# clem 17/10/2016
def get_response_opt(data=empty_dict, http_code=HTTP_SUCCESS, version=settings.API_VERSION, message=''):
	assert isinstance(data, dict)
	http_code = { 'api':
		{'version': version, },
		'result'       : http_code,
		'message'      : message,
		'time'         : time.time()
	}
	http_code.update(data)
	
	return HttpResponse(json.dumps(http_code), content_type=CT_JSON, status=http_code)


def make_http_code(a_bool):
	return HTTP_SUCCESS if a_bool else HTTP_FAILED


def make_message(a_bool):
	return CUSTOM_MSG[make_http_code(a_bool)]

##############
# COMMON VIEWS
##############


# clem 17/10/2016
def root(_):
	return get_response()


# clem 17/10/2016
def handler404(_):
	return get_response_opt(message='NOT FOUND', http_code=404)
