# imports from sub-modules (the order is CRITICAL)
from system import *
from pythonic import *
from my_logging import *
from file_system import *
from networking import *
import git
from object_cache import ObjectCache
import time
from time import sleep

# DO NOT HAVE ANY BREEZE NOR DJANGO RELATED CODE IN THIS MODULE
# this module is intended to have utilities function used in breeze, but must remain self-contained
# i.e. NO Breeze related code, no Django-specific code, no imports from Breeze nor Django


# TODO rewrite, as a class maybe ?
# clem 09/03/2016 contains code from from http://stackoverflow.com/a/3229493/5094389
def advanced_pretty_print(d, indent=0, open_obj=False, get_output=False):
	""" Prints a tree from a nested dict

	:type d: dict | list | basestring
	:type indent: int
	:type open_obj: bool
	:type get_output: bool
	:rtype: None | basestring
	"""

	buff = ''

	# clem 10/03/2016
	def get_iter(obj):
		if isinstance(obj, basestring):
			return obj
		if type(obj) in [dict, list] or hasattr(obj, 'iteritems') or hasattr(obj, '__iter__'):
			return obj
		if hasattr(obj, '__dict__'):
			if open_obj:
				return obj.__dict__
			else:
				return repr(obj)
		return list()

	# clem 10/03/2016
	def get_type(obj):
		res = str(type(obj)).partition("'")[2].partition("'")[0]
		return res if not res == 'instance' else ''

	# clem 10/03/2016
	def get_size(obj):
		try:
			return len(obj)
		except (TypeError, AttributeError):
			if hasattr(obj, 'bit_length'):
				return obj.bit_length()
		return '?'

	# clem 10/03/2016
	def extra_info(obj):
		a_type = get_type(obj)
		return ' <%s:%s>' % (a_type, get_size(obj)) if a_type else ''

	# clem 14/03/2016
	def out(content):
		if get_output:
			return content
		else:
			print content
			return ''

	def multi_line_ident(txt):
		return txt.replace('\n', '\n' + '\t' * (indent + 1))

	iterable = get_iter(d)

	if type(d) is list: # source element is a list, that may contain dicts
		i = 0
		for el in iterable:
			buff += out('\t' * indent + '_#%s :' % i)
			buff += str(advanced_pretty_print(el, indent + 1, open_obj, get_output))
			i += 1
	elif type(d) is dict or type(iterable) is dict:
		for key, value in iterable.iteritems():
			buff += out('\t' * indent + str(key) + extra_info(value))
			if isinstance(value, (dict, list)):
				buff += str(advanced_pretty_print(value, indent + 1, open_obj, get_output))
			else:
				buff += out('\t' * (indent + 1) + multi_line_ident(str(repr(value))))
	else:
		buff += out('\t' * (indent + 1) + multi_line_ident(str(iterable)))

	# if get_output:
	return buff


# clem 01/04/2016
def pp(data, unfold_objects=False, return_output=False):
	return advanced_pretty_print(data, open_obj=unfold_objects, get_output=return_output)


# clem 06/04/2016
def password_from_file(path):
	try:
		from os.path import exists, expanduser
		if not exists(path):
			temp = expanduser(path)
			if exists(temp):
				path = temp
		return open(path).read().replace('\n', '')
	except IOError:
		print 'error in readfile : %s' % path


# clem 06/05/2016, moved here on 16/05/2016
def gen_file_from_template(template_path, sub_dict, output_path=None, safe=True):
	""" generates a content from a template

	:param template_path: the path of the template file to use
		(c.f. https://docs.python.org/2.7/library/string.html#string.Template )
	:type template_path: str or unicode
	:param sub_dict: the substitution dictionary to use. Keys are used to match the $-var in the template
	:type sub_dict: dict
	:param output_path: the full path (including file name) where to save the output to. If None, then the
		result is returned
	:type output_path: basestring or None
	:param safe: If True, the sub-engine will not raise error for non-matched $-keys
	:type safe: bool
	:return: Either a success flag is output_path was provided, or the result of the replacement if successful,
	or False
	:rtype: bool or basestring
	"""
	from os.path import exists, expanduser
	assert isinstance(template_path, (str, unicode))
	assert exists(template_path)
	assert output_path is None or isinstance(output_path, (str, unicode))
	assert isinstance(sub_dict, dict)

	from string import Template

	# load the template
	with open(template_path) as template_fd:
		src = Template(template_fd.read())

	# do the substitution
	result = src.safe_substitute(sub_dict) if safe else src.substitute(sub_dict)

	if output_path:
		output_path = expanduser(output_path)
		with open(output_path, 'w') as output_fd:
			# writes the result to the output file
			while output_fd.write(result):
				pass
		return True
	return result


# moved from settings on 19/05/2016
# TODO make a generator
# FIXME Django Specific ?
def get_key(path=''):
	try:
		with open(path + 'secret') as f:
			return f.read()
	except Exception:
		pass
	return None
