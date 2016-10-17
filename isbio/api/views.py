from common import get_response


# clem 17/10/2016
def api_home(request):
	data = {'version': "1.0"}
	
	return get_response(data)
