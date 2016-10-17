from django.http import HttpResponse
import time
import json

CT_JSON = 'application/json'
empty_dict = dict()


# clem 17/10/2016
def get_response(data=empty_dict, result=200):
	assert isinstance(data, dict)
	result = {'api':
		{'version': '?', },
		'result': result,
		'message': '',
		'time': time.time()
	}
	result.update(data)
	
	return HttpResponse(json.dumps(result), content_type=CT_JSON)
