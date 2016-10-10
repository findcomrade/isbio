from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required # , permission_required
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from breeze.models import UserProfile # TODO move to a common base app
# from django.shortcuts import render
# from django.conf import settings
# from django.contrib import auth
# from django.shortcuts import redirect


@login_required(login_url='/')
def db_viewer(request):
	return render_to_response('dbviewer.html', RequestContext(request, {
		'dbviewer_status': 'active',
	}))


@login_required(login_url='/')
def db_policy(request):
	user_profile = UserProfile.objects.get(user=request.user)
	user_profile.db_agreement = True
	user_profile.save()
	# return HttpResponseRedirect('/dbviewer/') # FIXME hardcoded url
	return HttpResponseRedirect(reverse(db_viewer))


@login_required(login_url='/')
def home_paginate(request):
	if request.is_ajax() and request.method == 'GET':
		page = request.GET.get('page')
		table = request.GET.get('table')
		
		if table == 'screens':
			tag_symbol = 'screens'
			paginator = Paginator(rora.get_screens_info(), 15) # TODO check ref
			# paginator = Paginator(rora.get_dtm_screens(), 15)
			template = 'screens-paginator.html'
		elif table == 'datasets':
			tag_symbol = 'datasets'
			paginator = Paginator(rora.get_screens_info(), 15) # TODO check ref
			template = 'datasets-paginator.html'
		elif table == 'screen_groups':
			tag_symbol = 'screen_groups'
			paginator = Paginator(rora.get_screens_info(), 15) # TODO check ref
			# paginator = Paginator(rora.get_dtm_screen_groups(), 15)
			template = 'screen-groups-paginator.html'
		
		try:
			items = paginator.page(page)
		except PageNotAnInteger:  # if page isn't an integer
			items = paginator.page(1)
		except EmptyPage:  # if page out of bounds
			items = paginator.page(paginator.num_pages)
		
		return render_to_response(template, RequestContext(request, { tag_symbol: items }))
	else:
		return False
