from django.utils import timezone
from breeze.utils import pp
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
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
def get_response(data=empty_dict, result=200):
	assert isinstance(data, dict)
	result = {
		'api'    :
			{ 'version': VERSION, },
		'result' : result,
		'message': '',
		'time'   : timezone.now()
	}
	result.update(data)
	
	return HttpResponse(json.dumps(data), content_type=CT_JSON)


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
def git_hook(request):
	if request.POST:
		print(request.POST)
	else:
		print(request.GET)
	
	data = { 'msg': 'ok' }
	
	return get_response(data)
