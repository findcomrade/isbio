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
CT_TEXT = 'text/plain'
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
class MyWSGIReq(WSGIRequest):
	import hashlib
	import hmac as _hmac_lib
	H_SIG_HEADER = 'HTTP_X_HUB_SIGNATURE'
	H_REQ_METHOD = 'REQUEST_METHOD'
	H_C_T = 'CONTENT_TYPE'
	H_HOST = 'HTTP_HOST'
	H_REMOTE_IP = 'REMOTE_ADDR'
	H_USER_AGENT = 'HTTP_USER_AGENT'
	
	def __init__(self, request):
		assert isinstance(request, WSGIRequest)
		super(MyWSGIReq, self).__init__(request.environ)
	
	def hmac(self, key, algorithm=hashlib.sha1):
		return self._hmac_lib.new(key, self.body, algorithm).hexdigest() # data.encode('utf-8')

	def get_meta(self, key, default=''):
		return str(self.META.get(key, default))

	def get_meta_low(self, key, default=''):
		return self.get_meta(key, default).lower()
	
	def get_meta_up(self, key, default=''):
		return self.get_meta(key, default).upper()

	@property
	def signature(self):
		return self.get_meta(self.H_SIG_HEADER)
	
	@property
	def has_sig(self):
		return self.signature.startswith('sha1')
	
	@property
	def is_post_hook(self):
		return self.get_meta_up(self.H_REQ_METHOD) == 'POST'
	
	@property
	def is_json_post(self):
		return self.is_post_hook and self.get_meta_low(self.H_C_T) == CT_JSON

	@property
	def client_id(self):
		return '%s (%s) / %s' %\
			(self.get_meta(self.H_HOST), self.get_meta(self.H_REMOTE_IP), self.get_meta(self.H_USER_AGENT))

	def check_sig(self, key=None):
		if self.is_json_post and self.has_sig and self.body:
			if not key:
				key = get_key_magic(1)
			if self.signature.endswith(self.hmac(key)):
				logger.info('VERIFIED sig FROM %s' % self.client_id)
				return self.body
			else:
				logger.error('!! SIGNATURE MISMATCH FROM %s' % self.client_id)
		return False


# clem 17/10/2016
def get_json(request_init):
	request = MyWSGIReq(request_init)
	key = get_key_magic(1)
	try:
		json_data = request.check_sig(key)
		if json_data:
			return json.loads(json_data)
	except Exception as e:
		logger.exception(str(e))

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
	payload = get_json(request)
	if payload:
		# TODO filter json request
		import subprocess
		subprocess.Popen('sleep 2 && git pull', shell=True)
		return get_response(payload, message='ok')
		
	return get_response(result=400)
	
	
# clem 17/10/2016
@csrf_exempt
def git_hook(request):
	payload = get_json(request)
	if payload:
		# TODO filter json request
		return get_response(payload, message='ok')
	
	return get_response(result=400)
