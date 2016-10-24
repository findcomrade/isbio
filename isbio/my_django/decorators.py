from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect


# clem 24/10/2016 from https://djangosnippets.org/snippets/1703/
def group_required(*group_names):
	"""Requires user membership in at least one of the groups passed in."""
	
	def in_groups(u):
		if u.is_authenticated():
			if bool(u.groups.filter(name__in=group_names)) | u.is_superuser:
				return True
		return False
	
	return user_passes_test(in_groups)


# clem 24/10/2016 from  http://stackoverflow.com/a/6122181
def authors_only(function):
	def wrap(request, *args, **kwargs):
		
		profile = request.user.get_profile()
		if profile.usertype == 'Author':
			return function(request, *args, **kwargs)
		else:
			return HttpResponseRedirect('/')
	
	wrap.__doc__ = function.__doc__
	wrap.__name__ = function.__name__
	return wrap


# clem 24/10/2016
def admins_only(function):
	def wrap(request, *args, **kwargs):
		
		profile = request.user.get_profile()
		if profile.usertype == 'Author':
			return function(request, *args, **kwargs)
		else:
			return HttpResponseRedirect('/')
	
	wrap.__doc__ = function.__doc__
	wrap.__name__ = function.__name__
	return wrap
