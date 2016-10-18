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
def get_response(data=empty_dict, result=200, version=settings.API_VERSION, message=''):
	assert isinstance(data, dict)
	result = {'api':
		{'version': version, },
		'result': result,
		'message': message,
		'time': time.time()
	}
	result.update(data)
	
	return HttpResponse(json.dumps(result), content_type=CT_JSON)
