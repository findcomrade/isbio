from django.shortcuts import render
from django.conf import settings
from django.contrib import auth
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from utilz import logger, is_http_client_in_fimm_network, this_function_name
import json
import requests
# from django.contrib.auth.decorators import login_required
# import os


def index(request, template='hello_auth/base.html'):
	if not request.user.is_authenticated():
		error = request.GET.get('error', '')
		error_description = request.GET.get('error_description', '')
		context = {'from_fimm': is_http_client_in_fimm_network(request) }
		if error and error_description:
			# commit an error message
			messages.add_message(request, messages.ERROR, '%s : %s' % (error, error_description))
			return redirect(reverse(this_function_name()))
		# if an error message is present, consume it
		msg = messages.get_messages(request)
		if msg:
			context.update({ 'error_msg': msg})
		
		return render(request, template, context=context)
	else:
		return redirect(settings.AUTH0_SUCCESS_URL)


# TODO : use / extend auth0.auth_helpers instead
def process_login(request):
	""" Default handler to login user
	
	
	:param request: HttpRequest
	"""
	
	code = request.GET.get('code', '')
	if code:
		json_header = { 'content-type': 'application/json' }
		token_url = 'https://%s/oauth/token' % settings.AUTH0_DOMAIN
		
		token_payload = {
			'client_id'    : settings.AUTH0_CLIENT_ID,
			'client_secret': settings.AUTH0_SECRET,
			'redirect_uri' : settings.AUTH0_CALLBACK_URL,
			'code'         : code,
			'grant_type'   : 'authorization_code'
		}
		
		token_info = requests.post(token_url,
			data=json.dumps(token_payload),
			headers=json_header).json()
		
		if 'error' not in token_info:
			url = 'https://%s/userinfo?access_token=%s'
			user_url = url % (settings.AUTH0_DOMAIN, token_info['access_token'])
			user_info = requests.get(user_url).json()
			
			user = auth.authenticate(**user_info)
			assert isinstance(user, User)
			# We're saving all user information into the session
			request.session['profile'] = user_info
			
			if user and user.is_active:
				auth.login(request, user)
				logger.info('AUTH success for %s (%s)' % (user.username, user.email))
			else: # error from django auth (i.e. inactive user, or id mismatch)
				request.session['profile'] = None
				logger.warning('AUTH denied for %s (%s)' % (user.username, user.email))
				return HttpResponse(status=403)
		else: # error from AUTH0
			print(token_info)
			if token_info['error'] == 'access_denied':
				logger.warning('AUTH failure [%s]' % str(token_info))
				return HttpResponse(status=503)
	else:
		logger.warning('AUTH invalid GET[%s] POST[%s] content: %s' % (request.GET.__dict__,
		request.POST.__dict__, str(request.body)))
		print ('unsupported auth type :\n', request.GET.__dict__, request.POST.__dict__)
	
	return index(request)


def trigger_logout(request):
	""" Default handler to login user
	
	
	:param request: HttpRequest
	"""
	if request.user.is_authenticated():
		auth.logout(request)
		return redirect('%s?returnTo=%s' % (settings.AUTH0_LOGOUT_URL, settings.AUTH0_LOGOUT_REDIRECT))
		# return redirect('https://www.fimm.fi')
	else:
		return HttpResponse(status=503)
