from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpRequest
from breeze.utilities import *
import json
import time

# from breeze.utils import pp
# from django.core.urlresolvers import reverse
# from django.conf import settings
# from django import http
# from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
# from django.template.context import RequestContext
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

CT_JSON = 'application/json'
empty_dict = dict()
VERSION = '1.0'


# clem 17/10/2016
def get_key_magic(level=0):
	return get_key('api_' + this_function_caller_name(level))


# clem 17/10/2016
def get_response(data=empty_dict, result=200, message=''):
	assert isinstance(data, dict)
	result = {
		'api'    :
			{ 'version': VERSION, },
		'result' : result,
		'message': message,
		'time'   : time.time()
	}
	result.update(data)
	
	return HttpResponse(json.dumps(result), content_type=CT_JSON)


# clem 17/10/2016
def check_signature(request):
	assert isinstance(request, HttpRequest)
	# X-Hub-Signature: sha1=*
	print ('META', str(request.META))
	print ('X-Hub-Signature', request.META.get('X-Hub-Signature', None))
	
	key = get_key_magic(1)
	print ('key for %s : %s' % (this_function_caller_name(), key))
	
	payload = request.REQUEST.get('payload', None)
	if payload:
		print('payload :')
		pp(payload)
	return payload
	

#########
# VIEWS #
#########


# clem 17/10/2016
def root(_):
	data = { 'now': timezone.now()}
	
	return get_response(data)


# clem 17/10/2016
def hook(_):
	data = { 'msg': 'ok' }
	
	return get_response(data)


# clem 17/10/2016
@csrf_exempt
def reload_sys(request):
	payload = check_signature(request)
	if payload:
		# TODO filter json request
		data = { 'msg': 'ok' }
		import subprocess
		subprocess.Popen('sleep 2 && git pull', shell=True)
		return get_response(data, message='ok')
		
	return get_response(result=400, )
	
	
# clem 17/10/2016
@csrf_exempt
def git_hook(request):
	payload = check_signature(request)
	if payload:
		# TODO filter json request
		data = { 'msg': 'ok' }
		return get_response(data, message='ok')
	
	return get_response(result=400)
