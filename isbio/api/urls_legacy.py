from django.conf.urls import url
from . import views_legacy as legacy

urlpatterns = [
	url(r'^script-editor/get-content/(?P<content>[^/-]+)(?P<iid>-\d+)?/?$', legacy.show_templates,
		name='legacy.show_templates'),
]
