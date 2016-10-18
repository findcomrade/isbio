from django.conf.urls import url
from api import views_v1 as v1
# from . import views as hook

urlpatterns = [
	url(r'^$', v1.hook, name='v1.hook'),
	url(r'^git/?$', v1.git_hook, name='v1.git_hook'),
	url(r'^reload/?$', v1.reload_sys, name='v1.reload'),
]
