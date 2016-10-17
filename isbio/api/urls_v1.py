from django.conf.urls import url
from . import views_v1 as v1

urlpatterns = [
	url(r'^$', v1.root, name='v1.root'),
	url(r'^hook/?$', v1.hook, name='v1.hook'),
	url(r'^hook/git/?$', v1.git_hook, name='v1.git_hook'),
]
