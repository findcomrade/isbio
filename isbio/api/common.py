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
HTTP_NOT_IMPLEMENTED = 501
CUSTOM_MSG = {
	HTTP_SUCCESS: 'ok',
	HTTP_FAILED: 'error',
	HTTP_NOT_FOUND: 'NOT FOUND',
	HTTP_NOT_IMPLEMENTED: 'NOT IMPLEMENTED YET',
}


# clem 18/10/2016
def get_response(result=True, data=empty_dict, version=settings.API_VERSION):
	"""
	
	:param result: optional bool to return HTTP200 or HTTP400
	:type result: bool | None
	:param data: optional dict, containing json-serializable data
	:type data: dict | None
	:param version: optionally specify the version number to return or default
	:type version: str | None
	:rtype: HttpResponse
	"""
	return get_response_opt(data, make_http_code(result), version, make_message(result))
	

# clem 17/10/2016
def get_response_opt(data=empty_dict, http_code=HTTP_SUCCESS, version=settings.API_VERSION, message=''):
	"""
	
	:param data: optional dict, containing json-serializable data
	:type data: dict | None
	:param http_code: optional HTTP code to return (default is 200)
	:type http_code: int | None
	:param version: optionally specify the version number to return or default
	:type version: str | None
	:param message: if no message is provided, one will be generated from the HTTP code
	:type message: str | None
	:rtype: HttpResponse
	"""
	assert isinstance(data, dict)
	if not message:
		make_message(http_code=http_code)
	result = { 'api':
		{'version': version, },
		'result'       : http_code,
		'message'      : message,
		'time'         : time.time()
	}
	result.update(data)
	
	return HttpResponse(json.dumps(result), content_type=CT_JSON, status=http_code)


# clem 18/10/2016
def make_http_code(a_bool):
	return HTTP_SUCCESS if a_bool else HTTP_FAILED


# clem 18/10/2016
def make_message(a_bool=True, http_code=None):
	if not http_code:
		http_code = make_http_code(a_bool)
	return CUSTOM_MSG[http_code]


# clem 18/10/2016
def default_suspicious(request):
	raise SuspiciousOperation('Invalid request or handling error at %s (payload : %s)' % (request.path,
	len(request.body)))


##############
# COMMON VIEWS
##############


# clem 17/10/2016
def root(_):
	return get_response()


# clem 17/10/2016
def handler404(_):
	return get_response_opt(http_code=HTTP_NOT_FOUND)
