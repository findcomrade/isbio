from django.conf.urls import url, include
from . import views as api_views

urlpatterns = [
	url(r'^?$', api_views.api_home, name='api.home'),
	url(r'^legacy/$', include('api.views_legacy')),
	url(r'^v1/$', include('api.urls_v1')),
]
