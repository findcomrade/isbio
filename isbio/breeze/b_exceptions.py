from django.core.exceptions import PermissionDenied as PermissionDenied_org, ObjectDoesNotExist
from utilz import logger, this_function_caller_name
__author__ = 'clem'
__date__ = '25/05/2015'
#
# System checks
#


class SystemCheckFailed(RuntimeWarning):
	pass


class UrlFileHasMalformedPatterns(SystemCheckFailed):
	pass


class FileSystemNotMounted(SystemCheckFailed):
	pass


class MysqlDbUnreachable(BaseException):
	pass


class FileServerUnreachable(BaseException):
	pass


class NetworkUnreachable(SystemCheckFailed):
	pass


class InternetUnreachable(SystemCheckFailed):
	pass


class RORAUnreachable(SystemCheckFailed):
	pass


class RORAFailure(SystemCheckFailed):
	pass


class SGEImproperlyConfigured(SystemCheckFailed):
	pass


class DOTMUnreachable(SystemCheckFailed):
	pass


class ShinyUnreachable(SystemCheckFailed):
	pass


class NoSshTunnel(SystemCheckFailed):
	pass


class TargetNotResponding(SystemCheckFailed):
	pass


class DockerNotResponding(TargetNotResponding):
	pass


class WatcherIsNotRunning(SystemCheckFailed):
	pass


class SGEUnreachable(SystemCheckFailed):
	pass


class CASUnreachable(SystemCheckFailed):
	pass


class GlobalSystemChecksFailed(SystemError):
	pass
#
# END
#


class SGEError(RuntimeWarning):
	pass


class NoSuchJob(RuntimeWarning):
	pass


class InvalidArgument(BaseException):
	pass


class InvalidArguments(BaseException):
	pass


class ReadOnlyAttribute(RuntimeWarning):
	pass


class NotDefined(BaseException):
	pass


class ObjectNotFound(BaseException):
	pass


class FileNotFound(ObjectNotFound):
	pass


class ConfigFileNotFound(FileNotFound):
	pass


class ObjectHasNoReadOnlySupport(RuntimeError):
	pass


class PermissionDenied(PermissionDenied_org):
	def __init__(self, *args, **kwargs):
		super(PermissionDenied, self).__init__(*args, **kwargs)
		from django.core.handlers.wsgi import WSGIRequest
		final_text = ''
		request = kwargs.get('request', None) or args[0] if len(args) >= 1 else None
		message = kwargs.get('message', '') or kwargs.get('msg', '') or args[0] if len(args) >= 1 else ''
		if isinstance(request, WSGIRequest):
			final_text = 'Access denied to %s for %s' % (request.user.username, this_function_caller_name())
		if message and isinstance(message, basestring):
			if final_text:
				message = ' (%s)' % message
			final_text += message
		logger.warning(final_text)

