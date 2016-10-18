from django.conf.urls import url, include
from . import views_v1 as v1

urlpatterns = [
	url(r'^$', v1.root, name='v1.root'),
	url(r'^hook/?$', include('webhooks.urls'))
]
