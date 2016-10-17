from django.http import HttpResponse
from django.utils import timezone
from breeze.utils import pp
from django.views.decorators.csrf import csrf_exempt
import json

# from django.core.urlresolvers import reverse
# from django.conf import settings
# from django import http
# from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
# from django.template.context import RequestContext
# from django.contrib.auth.decorators import login_required
# from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

CT_JSON = 'application/json'


# clem 17/10/2016
def root(_):
	data = { 'now': timezone.now()}
	
	return HttpResponse(json.dumps(data), content_type=CT_JSON)


# clem 17/10/2016
def hook(_):
	data = { 'msg': 'ok' }
	
	return HttpResponse(json.dumps(data), content_type=CT_JSON)


# clem 17/10/2016
@csrf_exempt
def git_hook(request):
	if request.POST:
		pp(request.POST)
	else:
		pp(request.GET)
	
	data = { 'msg': 'ok' }
	
	return HttpResponse(json.dumps(data), content_type=CT_JSON)
