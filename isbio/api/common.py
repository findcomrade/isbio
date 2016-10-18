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


# clem 17/10/2016
def get_response(data=empty_dict, http_code=200, version=settings.API_VERSION, message=''):
	assert isinstance(data, dict)
	http_code = { 'api':
		{'version': version, },
		'result'       : http_code,
		'message'      : message,
		'time'         : time.time()
	}
	http_code.update(data)
	
	return HttpResponse(json.dumps(http_code), content_type=CT_JSON, status=http_code)


# clem 17/10/2016
def root(_):
	data = { }
	
	return get_response(data, message='ok')


# clem 17/10/2016
def handler404(_):
	return get_response(message='NOT FOUND', http_code=404)
