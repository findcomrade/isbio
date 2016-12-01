"""CAS authentication backend override"""
from django_cas_ng.backends import CASBackend as org_CASBackend
from django.contrib.auth.backends import ModelBackend


class CASBackend(org_CASBackend):
	"""CAS authentication backend override"""
	user_can_authenticate = ModelBackend.user_can_authenticate

