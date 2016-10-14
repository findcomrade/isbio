from . import Thread
import gc
import inspect

__version__ = '0.1.1'
__author__ = 'clem'
__date__ = '27/05/2016'


# clem 05/04/2016
def new_thread(func):
	""" Wrapper to run functions in a new Thread (use as a @decorator)

	:type func:
	:rtype:
	"""

	# assert callable(func)

	def decorated(*args):
		Thread(target=func, args=args).start()

	return None if not func else decorated


# clem 08/04/2016
def is_from_cli():
	""" Tells if the caller was called from command line or not

	:rtype: bool
	"""
	return this_function_caller_name(1) == '<module>'


# clem 08/04/2016
def get_named_tuple(class_name, a_dict):
	# noinspection PyCompatibility
	assert isinstance(class_name, basestring) and isinstance(a_dict, dict)
	from collections import namedtuple
	return namedtuple(class_name, ' '.join(a_dict.keys()))(**a_dict)


# moved from settings on 19/05/2016
def recur_rec(nb, function, args):
	if nb > 0:
		return recur_rec(nb - 1, function, function(args))
	return args


# moved from settings on 19/05/2016
def recur(nb, function, args):
	while nb > 0:
		args = function(args)
		nb -= 1
	return args


# moved in utils on 19/05/2016
def not_imp(self): # writing shortcut for abstract classes
	raise NotImplementedError("%s was not implemented in concrete class %s." % (
		this_function_caller_name(), self.__class__.__name__))


# clem 27/05/2016
class ClassProperty(property):
	def __get__(self, cls, owner=None):
		return classmethod(self.fget).__get__(None, owner)()


# clem 10/10/2016 from http://stackoverflow.com/a/4506081/5094389
def this_function_own_object_old():
	""" Return the function object of the caller
	
	:rtype: function
	"""
	frame = inspect.currentframe(1)
	code = frame.f_code
	globs = frame.f_globals
	functype = type(lambda: 0)
	funcs = []
	for func in gc.get_referrers(code):
		if type(func) is functype:
			if getattr(func, "func_code", None) is code:
				if getattr(func, "func_globals", None) is globs:
					funcs.append(func)
					if len(funcs) > 1:
						return None
	return funcs[0] if funcs else None


lambda_cache = { }


def this_function_own_object(*args, **kw):
	from types import FunctionType
	caller_frame = currentframe(1)
	code = caller_frame.f_code
	if not code in lambda_cache:
		lambda_cache[code] = FunctionType(code, caller_frame.f_globals)
	return lambda_cache[code](*args, **kw)


# clem 08/04/2016
def this_function_name(delta=0):
	""" Return the name of the calling function
	
	:param delta: change the depth of the call stack inspection
	:type delta: int
	
	:rtype: str
	"""
	return this_function_caller_name(delta)


# clem 08/04/2016 + 10/10/2016
def this_function_caller_name(delta=0):
	""" Return the name of the calling function's caller
	
	:param delta: change the depth of the call stack inspection
	:type delta: int
	
	:rtype: str
	"""
	return inspect.currentframe(2 + delta).f_code.co_name
