from django.conf.urls import url
from . import views as api_views
from . import views_legacy as legacy
from . import views_v1 as v1

urlpatterns = [
	url(r'^api/?$', api_views.api_home, name='api.home'),
	url(r'^api/legacy/script-editor/get-content/(?P<content>[^/-]+)(?P<iid>-\d+)??$',
		legacy.show_templates, name='legacy.show_templates'),
	url(r'^api/v1/?$', v1.root, name='v1.root'),
	url(r'^api/v1/hook/?$', v1.hook, name='v1.hook'),
	url(r'^api/v1/hook/git/?$', v1.git_hook, name='v1.git_hook'),
]
