from django.http import HttpResponse
import json

CT_JSON = 'application/json'


# clem 17/10/2016
def api_home(request):
	data = {'version': "1.0"}
	
	return HttpResponse(json.dumps(data), content_type=CT_JSON)
