from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
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
def hmac(data, key):
	import hmac
	import hashlib
	
	# digest_maker = hmac.new(bytearray(key, 'utf-8'), bytearray(data, 'utf-8'), hashlib.sha1)
	digest_maker = hmac.new(key, data, hashlib.sha1) #  data.encode('utf-8')
	# digest_maker.update(data)
	return digest_maker.hexdigest()


# clem 17/10/2016
def check_signature(request):
	assert isinstance(request, WSGIRequest)
	sig = request.META.get('HTTP_X_HUB_SIGNATURE', '')
	host = request.META.get('REMOTE_HOST', '')
	agent = request.META.get('HTTP_USER_AGENT', '')
	this_id = '%s / %s' % (host, agent)
	# HTTP_USER_AGENT
	raw_body = request.body
	#  = json.loads(request.body)
	# payload = request.POST.get('payload', None)
	if sig and raw_body:
		# print('sig:', sig)
		key = get_key_magic(1)
		digest = hmac(raw_body, key)
		if sig.startwith('sha1') and sig.endswith(digest):
			logger.info('VERIFIED SIG FROM %s' % this_id)
			return json.loads(raw_body)
		else:
			logger.error('SIGNATURE MISMATCH' % this_id)
	return None
	

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
		import subprocess
		subprocess.Popen('sleep 2 && git pull', shell=True)
		return get_response(payload, message='ok')
		
	return get_response(result=400, )
	
	
# clem 17/10/2016
@csrf_exempt
def git_hook(request):
	payload = check_signature(request)
	if payload:
		# TODO filter json request
		return get_response(payload, message='ok')
	
	return get_response(result=400)
