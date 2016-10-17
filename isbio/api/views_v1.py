from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import SuspiciousOperation
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
	H_SIG = 'HTTP_X_HUB_SIGNATURE'
	H_DELIVERY_ID = 'X_GitHub_Delivery'
	H_REQ_METHOD = 'REQUEST_METHOD'
	H_C_T = 'CONTENT_TYPE'
	H_HOST = 'HTTP_X_Forwarded_For' # X-Forwarded-For # HTTP_HOST
	H_REMOTE_IP = 'HTTP_X_Real_IP' # X-Real-IP #
	H_USER_AGENT = 'HTTP_USER_AGENT'
	
	def __init__(self, request, call_depth=0):
		assert isinstance(request, WSGIRequest)
		super(MyWSGIReq, self).__init__(request.environ)
		self._call_depth = call_depth + 1
	
	def hmac(self, key, algorithm=hashlib.sha1):
		return self._hmac_lib.new(key, self.body, algorithm).hexdigest() # data.encode('utf-8')

	def get_meta(self, key, default=''):
		return str(self.META.get(key.upper(), default))

	def get_meta_low(self, key, default=''):
		return self.get_meta(key, default).lower()
	
	def get_meta_up(self, key, default=''):
		return self.get_meta(key, default).upper()

	@property
	def signature(self):
		return self.get_meta(self.H_SIG)
	
	@property
	def delivery_id(self):
		return self.get_meta(self.H_DELIVERY_ID)
	
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
				key = get_key_magic(self._call_depth)
			args = (this_function_caller_name(self._call_depth), self.client_id, self.delivery_id)
			msg = ' SIG_CHECK for %s FROM %s (delivery %s)' % args
			if self.signature.endswith(self.hmac(key)):
				success_msg = 'VERIFIED' + msg
				logger.info(success_msg)
				print (TermColoring.ok_green(success_msg))
				return self.body
			else:
				error_msg = 'FAILED' + msg
				logger.error(error_msg)
				print (TermColoring.fail(error_msg))
		return False


# clem 17/10/2016
def get_json(request_init):
	request = MyWSGIReq(request_init, 1)
	# key = get_key_magic(1)
	try:
		json_data = request.check_sig()
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
		if True:# TODO filter json request
			import subprocess
			subprocess.Popen('sleep 1 && git pull', shell=True)
			
			logger.info('Received system reload from GitHub, pulling and reloading ...')
			print (TermColoring.ok_blue('sleep 1 && git pull'))
			
			return get_response(payload, message='ok')
		
		raise SuspiciousOperation('Invalid request or handling error')
	
	
# clem 17/10/2016
@csrf_exempt
def git_hook(request):
	payload = get_json(request)
	if payload:
		if True: # TODO filter json request
			logger.info('Received git push event for R code')
			logger.warning('NOT_IMPLEMENTED')
			print ('NOT_IMPLEMENTED : R PULL')
			
			return get_response(payload, message='ok')
	
	raise SuspiciousOperation('Invalid request or handling error')
