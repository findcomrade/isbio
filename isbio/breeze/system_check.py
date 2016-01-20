from breeze import utils
from utils import Bcolors
from utils import logger_timer
from breeze.auxiliary import proxy_to
from django.conf import settings
from breeze.b_exceptions import *
from django.http import HttpRequest
from collections import OrderedDict

# from django.contrib.auth.models import User
# from _ctypes_test import func
# import breeze.auxiliary as aux


DEBUG = True
SKIP_SYSTEM_CHECK = False
# FAIL_ON_CRITICAL_MISSING = True
# RAISE_EXCEPTION = False
# ONLY_WAIT_FOR_CRITICAL = True # if checker should also wait for non-criticals

if DEBUG:
	# quick fix to solve PyCharm Django console environment issue
	from breeze.process import Process
else:
	from multiprocessing import Process

OK = '[' + Bcolors.ok_green('OK') + ']'
BAD = '[' + Bcolors.fail('NO') + ']'
WARN = '[' + Bcolors.warning('NO') + ']'


# clem 25/09/2015
class CheckerList(list):
	""" list of SysCheckUnit with filtering properties """
	FAIL_ON_CRITICAL_MISSING = True
	ONLY_WAIT_FOR_CRITICAL = True # if checker should also wait for non-criticals

	def __init__(self, check_list):
		self._list_to_check = check_list
		self._results = dict()
		super(CheckerList, self).__init__()

	@property
	def runnings(self):
		""" list of still active SysCheckUnit
		:rtype: list
		"""
		new = list()
		for each in self:
			assert isinstance(each, SysCheckUnit)
			if each.running:
				new.append(each)
		return new

	@property
	def article(self):
		return 'is' if len(self.runnings) == 1 else 'are'

	@property
	def running_count(self):
		return len(self.runnings)

	@property
	def any_running(self):
		return self.running_count > 0

	@property
	def boot_tests(self):
		"""
		list of test that are to be run at boot
		:rtype: list
		"""
		result = list()
		for each in self._list_to_check:
			if each.type in [RunType.both, RunType.boot_time]:
				result.append(each)
		return result

	@property
	def suceeded(self):
		# return len([x for x in self._results if self._results[x] == True])
		result = list()
		for each in self.boot_tests:
			if self._results[each.url]:
				result.append(each)
		return result

	def check_list(self):
		""" Boot-time run for all system checks
		"""
		for each in self._list_to_check:
			self._results[each.url] = False
			if each.s_check():
				self.append(each)

	def rendez_vous(self, wait_for_all=not ONLY_WAIT_FOR_CRITICAL): # Rendez-vous for processes
		"""
		wait for all process in the list to complette
		New version, replaces the 08/09/2015 one, better use of OOP
		"""
		for each in self[:]:
			assert isinstance(each, SysCheckUnit) and each.has_proc
			# Only wait for mandatory checks
			if wait_for_all or each.mandatory:
				each.block()
				self._results[each.url] = each.exitcode == 0
				if self.FAIL_ON_CRITICAL_MISSING and each.exitcode != 0 and each.mandatory:
					print Bcolors.fail('BREEZE INIT FAILED ( %s )' % repr(each.ex()))
					# raise each.ex()
					import sys
					sys.exit(2)
				each.terminate()
				self.remove(each)

		# print self._results
		for each in self:
			self._results[each.url] = each.exitcode == 0

		success_text = 'successful : %s/%s' % (len(self.suceeded) + 1, len(self.boot_tests) + 1)

		if not self.any_running:
			print Bcolors.ok_green('System is up and running, All checks done ! (%s)' % success_text)
		else:
			print Bcolors.ok_green('System is up and running, %s, ') % success_text + \
				Bcolors.warning('but %s (non critical) check%s %s still running %s') % \
				(self.running_count, 's' if self.running_count > 1 else '', self.article,
				self.runnings)


# Manage checks process for rendez-vous
# checking_list = CheckerList()


# clem 08/09/2015
class RunType:
	@staticmethod
	def runtime():
		pass

	@staticmethod
	def boot_time():
		pass

	@staticmethod
	def both():
		pass

	@staticmethod
	def disabled():
		pass


# clem 08/09/2015
class SysCheckUnit(Process):
	""" Describe a self executable unit of system test, includes all the process management part """
	RAISE_EXCEPTION = True

	def __init__(self, funct, url, legend, msg, type, t_out=0, arg=None, supl=None, ex=SystemCheckFailed,
				mandatory=False, long_poll=False):
		"""
		init Arguments :
		funct: the function to run to asses test result
		url: id of test, and url part to access it
		legend: title to display on WebUI
		msg: title to display on Console
		type: type of this test
		t_out: timeout to set test as failed
		arg: arguments to funct
		supl: a function to run after this test
		ex: an exception to eventually raise on check failure
		mandatory: is this test success is required to system consistent boot

		:param funct: the function to run to asses test result
		:type funct: callable
		:param url: id of test, and url part to access it
		:type url: str
		:param legend: title to display on WebUI
		:type legend: str
		:param msg: title to display on Console
		:type msg: str
		:param type: type of this test
		:type type: RunType.property
		:param t_out: timeout to set test as failed
		:type t_out: int
		:param arg: arguments to funct
		:type arg:
		:param supl: a function to run after this test
		:type supl: callable
		:param ex: an exception to eventually raise on check failure
		:type ex: Exception
		:param mandatory: is this test success is required to system consistent boot
		:type mandatory: bool
		"""
		if type is RunType.runtime or callable(funct):
			self.checker_function = funct
			self.url = url
			self.legend = legend
			self._msg = msg
			self.t_out = int(t_out)
			self.arg = arg
			self.type = type
			self.supl = supl
			self.mandatory = mandatory
			self.ex = ex
			self.lp = long_poll
			# self._process = Process
		else:
			raise InvalidArgument(Bcolors.fail('Argument function must be a callable object'))

	def s_check(self):
		if (self.type is RunType.boot_time or self.type is RunType.both) and callable(self.checker_function):
			return self.split_run()
		return False

	# clem 25/09/2015
	@property
	def has_proc(self):
		return isinstance(self, Process)

	# clem 25/09/2015
	@property
	def running(self):
		return self.has_proc and self.is_alive()

	# clem 25/09/2015
	def block(self):
		if self.running:
			self.join()

	# clem 08/09/2015
	def split_run(self, from_ui=False):
		"""
		Runs checker function in a separate process for
			_ concurrency and speed (from console)
			_ process isolation, and main thread segfault avoidance (from UI)
		"""
		super(SysCheckUnit, self).__init__(target=self.split_runner, args=(from_ui,))
		self.start()
		if not from_ui:
			# checking_list.append(self) # add process to the rendez-vous list
			return True
		else:
			self.block() # wait for process to finish
			try:
				self.terminate()
			except AttributeError:
				pass
			return self.exitcode == 0

	# clem 08/09/2015
	def split_runner(self, from_ui=False):
		"""
		Checker function runner.
		Call the function, display console message and exception if appropriate
		"""
		res = False
		if callable(self.checker_function):
			try:
				if self.arg is not None:
					res = self.checker_function(self.arg)
				else:
					res = self.checker_function()
			except Exception as e:
				self.ex = e
				pass
		else:
			raise InvalidArgument(Bcolors.fail('Argument function must be a callable object'))

		sup = ''
		sup2 = ''

		if not res:
			if self.mandatory:
				sup2 = Bcolors.warning('required and critical !')
			else:
				sup2 = Bcolors.warning('NOT critical')

		if not from_ui:
			print self.msg,
			if self.supl is not None and callable(self.supl):
				sup = self.supl()
			print OK if res else BAD if self.mandatory else WARN, sup, sup2

		if not res:
			import sys
			if self.RAISE_EXCEPTION and not from_ui:
				raise self.ex
			if from_ui or self.mandatory:
				sys.exit(1)
			sys.exit(2)
		# implicit exit(0)

	@property
	def msg(self):
		return Bcolors.ok_blue(self._msg)

	# clem 25/09/2015
	def __repr__(self):
		return '<SysCheckUnit %s>' % self.url


# clem 08/09/2015
# DEL check_rdv() on 25/09/2015 replaced by checking_list.rendez_vous()


# clem 08/09/2015
@logger_timer
def run_system_test():
	"""
	NEW ONE 08/09/2015
	replacing old version from 31/08/2015
	"""
	from breeze.middlewares import is_on
	global SKIP_SYSTEM_CHECK
	if not SKIP_SYSTEM_CHECK and is_on():
		print Bcolors.ok_blue('Running Breeze system integrity checks ......')
		if fs_mount.checker_function():
			print fs_mount.msg + OK
			checking_list = CheckerList(CHECK_LIST)
			checking_list.check_list()
			checking_list.rendez_vous()
		else:
			print fs_mount.msg + BAD
			raise FileSystemNotMounted
	else:
		print Bcolors.ok_blue('Skipping Breeze system integrity checks ......')

##
# Special file system snapshot and checking systems
##


# clem 10/09/2015
def gen_test_report(the_user, gen_number=10, job_duration=30, time_break=1):
	from breeze.views import report_overview
	import time

	posted = dict()
	posted["project"] = 1
	posted["Section_dbID_9"] = 0
	posted["9_opened"] = 'False'
	posted["Dropdown"] = 'Enter'
	posted["Textarea"] = ''
	posted["Section_dbID_81"] = 0
	posted["81_opened"] = 'False'
	posted["Section_dbID_118"] = '1'
	posted["118_opened"] = 'True'
	posted["sleep duration"] = str(job_duration)
	posted["sleep_duration"] = str(job_duration)
	posted["wait_time"] = str(job_duration)
	posted["Groups"] = ''
	posted["Individuals"] = ''

	rq = HttpRequest()
	# del rq.POST
	rq.POST = posted
	rq.user = the_user
	rq.method = 'POST'

	for i in range(1, gen_number + 1):
		name = 'SelfTest%s' % i
		print name
		report_overview(rq, 'TestPipe', name, '00000')
		time.sleep(time_break)

	print 'done.'


# clem on 21/08/2015
def generate_file_index(root_dir, exclude=list(), start_id=0):
	"""
	Generate a dict with md5 checksums of every files within rootDir
	:param root_dir: path to scan
	:type root_dir: str
	:param exclude: list of folder within rootDir to exclude
	:type exclude: list
	:rtype: dict
	"""
	from os import walk
	from os.path import getmtime, join

	md5s = OrderedDict()

	def short(dir_name):
		if dir_name != root_dir:
			return dir_name.replace(root_dir, '') # if rootDir != dirName else './'
		else:
			return ''

	for dirName, subdirList, fileList in sorted(walk(root_dir)):
		# subdirList.sort()
		s_dir_name = short(dirName)
		if dirName not in exclude and '/.' not in s_dir_name and not s_dir_name.startswith('.'):
			# fileList.sort()
			for fname in fileList:
				start_id += 1
				md = utils.get_file_md5(join(dirName, fname))
				try:
					mod_time = getmtime(join(dirName, fname))
				except OSError:
					mod_time = ''
				md5s[join(s_dir_name, fname)] = [md, mod_time, start_id]

	return md5s, start_id


# clem on 21/08/2015
def save_file_index():
	"""
	Save the FS signature in file settings.FS_SIG_FILE
	and a file system checksum index json object in file settings.FS_LIST_FILE
	:return: True
	:rtype: bool
	"""
	from django.utils import simplejson

	fs_sig, save_obj = file_system_check()

	with open(settings.FS_SIG_FILE, 'w') as f:
		f.write(fs_sig)
	with open(settings.FS_LIST_FILE, 'w') as f:
		simplejson.dump(save_obj, f)

	return True


# clem on 21/08/2015
def file_system_check(verbose=False):
	"""
	Generate MD5 for files of every folders listed under settings.FOLDERS_TO_CHECK
	:param verbose: display info
	:type verbose: bool
	:return: file system signature, file system index dict
	:rtype: str, dict
	"""
	from django.utils import simplejson
	total = ''
	# save_obj = dict()
	save_obj = OrderedDict()
	last_id = 0
	for each in settings.FOLDERS_TO_CHECK:
		md5s, last_id = generate_file_index(each, ['__MACOSX', ], last_id)
		json = simplejson.dumps(md5s)
		# save_obj[each] = (utils.get_md5(json), md5s)
		save_obj[each] = md5s
		total += json
	# print '(' + str(len(md5s)), 'files)', fs_state[each]
	if verbose:
		for el in save_obj:
			print save_obj[el], el

	return utils.get_md5(total), save_obj


# clem on 21/08/2015
def saved_fs_sig():
	with open(settings.FS_SIG_FILE) as f:
		txt = f.readline()
	return txt


# clem on 21/08/2015
def check_is_file_system_unchanged():
	"""
	Check if the FS (as listed in settings.FOLDERS_TO_CHECK) remains unchanged
	:rtype: bool
	"""
	if file_system_check()[0] == saved_fs_sig():
		return True, True, 0
	else: # if both fs_sig don't match, review the whole fs. For example Newer or Added files don't count
		changed, broken, _, _, errors = deep_fs_check()
		return not changed, not broken, errors


##
# Checkers functions, called on boot and/or runtime
##


# clem 25/08/2015
@logger_timer
def deep_fs_check(fix_file_perm=False): # TODO optimize (too slow)
	"""
	Return flag_changed, flag_invalid, files_state, folders_state
	:return: flag_changed, flag_invalid, files_state, folders_state
	:rtype:
	"""
	from os.path import join, basename, dirname

	files_state = list()
	folders_state = list()
	current_state = file_system_check()[1]
	saved_state = utils.saved_fs_state()
	flag_changed = False
	flag_invalid = False
	errors = 0
	folder = OrderedDict()

	current_state = OrderedDict(sorted(current_state.items(), key=lambda t: t[0]))
	saved_state = OrderedDict(sorted(saved_state.items(), key=lambda t: t[0]))

	for each in saved_state:
		status = OrderedDict()
		status['name'] = each
		status['size'] = 0
		if each not in current_state:
			status['status'] = 'MISSING'
			flag_changed = True
			errors += len(saved_state[each])
		else:
			folder_count = len(saved_state[each])
			folder_size = utils.human_readable_byte_size(utils.get_folder_size(each))
			folder[each] = { 'count': folder_count, 'size': folder_size }
			status['count'] = folder_count
			status['size'] = folder_size
			if saved_state[each] == current_state[each]:
				status['status'] = 'OK'
			else:
				status['status'] = 'CHANGED'
				flag_changed = True
			# del current_state[each]
		folders_state.append(status)

	for each in saved_state:
		files_tmp = list()
		# ss = saved_state[each]
		ss = OrderedDict(sorted(saved_state[each].items(), key=lambda t: t[0]))
		# cs = current_state[each]
		cs = OrderedDict(sorted(current_state[each].items(), key=lambda t: t[0]))
		for file_n in ss:
			status = dict()
			file_path = join(each, file_n)
			status['name'] = basename(file_n)
			status['folder'] = dirname(file_n)
			if file_n not in cs:
				status['readable'] = True
				status['status'] = 'MISSING'
				errors += 1
				flag_changed = True
			else:
				status['readable'] = utils.is_readable(file_path)
				if ss[file_n] == cs[file_n]:
					status['status'] = 'OK'
				else:
					flag_changed = True
					if ss[file_n][1] > cs[file_n][1]:
						status['status'] = 'OLDER'
						errors += 1
					elif ss[file_n][1] < cs[file_n][1]:
						status['status'] = 'NEWER'
					else: # same time, different checksum, happens when file permission are changed
						status['status'] = 'EQT_DIFF'
						errors += 1
				del cs[file_n]
			if not status['readable']:
				status['id'] = ss[file_n][2]
			files_tmp.append(status.copy())
		# at this point cs should be empty
		for file_n in cs:
			status = OrderedDict()
			file_path = join(each, file_n)
			flag_changed = True
			status['name'] = basename(file_n)
			status['folder'] = dirname(file_n)
			status['status'] = 'ADDED'
			status['readable'] = utils.is_readable(file_path)
			if not status['readable']:
				if fix_file_perm:
					status['readable'] = utils.set_file_acl(file_path, silent_fail=True)
				else:
					status['id'] = ss[file_n][2]
			files_tmp.append(status)
		# files_tmp.insert(0, status.copy())
		# files_tmp = [status.copy()] + files_tmp
		files_state.append({ 'name': each, 'size': folder[each]['size'], 'count': len(files_tmp), 'list': files_tmp })

	if errors > 0:
		flag_invalid = True

	return flag_changed, flag_invalid, files_state, folders_state, errors


# clem on 20/08/2015
def check_rora():
	"""
	Check if RORA db host is online and RORA db connection is successful
	:rtype: bool
	"""
	try:
		if utils.is_host_online(settings.RORA_SERVER_IP, '2'):
			from breeze import rora
			return rora.test_rora_connect()
	except Exception as e:
		print e
	return False


# clem on 20/08/2015
def check_dotm():
	"""
	Check if Dotmatix db host is online and Dotmatix db connection is successful
	:rtype: bool
	"""
	# return status_button(rora.test_dotm_connect())
	if utils.is_host_online(settings.DOTM_SERVER_IP, 2):
		from breeze import rora
		return rora.test_dotm_connect()
	return False


# clem on 21/08/2015
def check_file_server():
	"""
	Check if file server host is online
	:rtype: bool
	"""
	return utils.is_host_online(settings.FILE_SERVER_IP, 2)


# clem on 21/08/2015
def check_file_system_mounted():
	"""
	Check if file server host is online, and project folder is mounted
	:rtype: bool
	"""
	from utils import exists
	return check_file_server() and exists(settings.MEDIA_ROOT)


# clem on 20/08/2015
def check_shiny(request):
	"""
	Check if Shiny server is responding
	:rtype: bool
	"""
	try:
		r = proxy_to(request, '', settings.SHINY_LOCAL_LIBS_TARGET_URL, silent=True, timeout=2)
		if r.status_code == 200:
			return True
	except Exception:
		pass
	return False


# clem on 22/09/2015
def check_csc_shiny(request):
	"""
	Check if CSC Shiny server is responding
	:rtype: bool
	"""
	try:
		r = proxy_to(request, '', settings.SHINY_REMOTE_LIBS_TARGET_URL, silent=True, timeout=4)
		if r.status_code == 200:
			return True
		else:
			print 'prox to', settings.SHINY_REMOTE_LIBS_TARGET_URL, r.status_code
	except Exception as e:
		pass
	return False


# clem on 23/09/2015
def check_csc_mount():
	"""
	Check if remote Shiny is mounted as part of the FS
	:rtype: bool
	"""
	from os import path
	try:
		if path.exists(settings.SHINY_REMOTE_LOCAL_PATH) and path.isdir(settings.SHINY_REMOTE_REPORTS):
			return True
	except Exception:
		pass
	return False


# clem on 20/10/2015
def check_csc_taito_mount():
	"""
	Check if remote Shiny is mounted as part of the FS
	:rtype: bool
	"""
	from os import path
	try:
		if path.exists(settings.TMP_CSC_TAITO_MOUNT) and path.isdir(
			settings.TMP_CSC_TAITO_MOUNT + settings.TMP_CSC_TAITO_REPORT_PATH):
			return True
	except Exception:
		pass
	return False


# clem on 09/09/2015
def check_watcher():
	from breeze.middlewares import JobKeeper
	return JobKeeper.p.is_alive()


# clem 08/09/2015
def check_cas(request):
	"""
	Check if CAS server is responding
	:rtype: bool
	"""
	if utils.is_host_online(settings.CAS_SERVER_IP, 2):
		try:
			r = proxy_to(request, '', settings.CAS_SERVER_URL, silent=True, timeout=3)
			if r.status_code == 200:
				return True
		except Exception:
			pass
	return False


# clem 09/09/2015
def ui_checker_proxy(what):
	"""	Run a self-test based on requested URL
	:param what: url of the system test
	:type what: str
	:return: If test is successful
	:rtype: bool
	"""
	if what not in CHECK_DICT:
		from breeze import auxiliary as aux
		return aux.fail_with404(HttpRequest(), 'NOT FOUND')
	obj = CHECK_DICT[what]
	assert isinstance(obj, SysCheckUnit)

	if obj.type in [RunType.both, RunType.runtime]:
		if obj.checker_function is check_watcher or obj.lp:
			return obj.checker_function()
		else:
			return obj.split_run(from_ui=True)
	return False


# clem 25/09/2015
def long_poll_waiter():
	from time import sleep
	sleep(settings.LONG_POLL_TIME_OUT_REFRESH)
	return 'ok'


# TODO FIXME runtime fs_check slow and memory leak ?
fs_mount = SysCheckUnit(check_file_system_mounted, 'fs_mount', 'File server', 'FILE SYSTEM\t\t ', RunType.runtime,
						ex=FileSystemNotMounted, mandatory=True)

proto = settings.SHINY_REMOTE_PROTOCOL.upper()

# Collection of system checks that is used to run all the test automatically, and display run-time status
CHECK_LIST = [
	SysCheckUnit(long_poll_waiter, 'breeze', 'Breeze HTTP', '', RunType.runtime, long_poll=True),
	# # SysCheckUnit(long_poll_waiter, 'breeze-dev', 'Breeze-dev HTTP', '', RunType.runtime, long_poll=True),
	SysCheckUnit(save_file_index, 'fs_ok', 'File System', 'saving file index...\t', RunType.boot_time, 25000,
				supl=saved_fs_sig, ex=FileSystemNotMounted, mandatory=True), fs_mount,
	SysCheckUnit(check_cas, 'cas', 'CAS server', 'CAS SERVER\t\t', RunType.both, arg=HttpRequest(), ex=CASUnreachable,
				mandatory=True),
	SysCheckUnit(check_rora, 'rora', 'RORA db', 'RORA DB\t\t\t', RunType.both, ex=RORAUnreachable),
	# SysCheckUnit(check_sge_c, 'sge_c', 'SGE conf', 'SGE CONFIG\t\t', RunType.boot_time, ex=SGEImproperlyConfigured,
	# 			mandatory=True),
	# SysCheckUnit(check_sge, 'sge', 'SGE DRMAA', 'SGE MASTER\t\t', RunType.both, ex=SGEUnreachable,
	# 			mandatory=True),
	SysCheckUnit(check_dotm, 'dotm', 'DotMatics server', 'DOTM DB\t\t\t', RunType.both, ex=DOTMUnreachable),
	SysCheckUnit(check_shiny, 'shiny', 'Local Shiny HTTP server', 'LOC. SHINY HTTP\t\t', RunType.runtime,
				arg=HttpRequest(), ex=ShinyUnreachable),
	SysCheckUnit(check_csc_shiny, 'csc_shiny', 'CSC Shiny %s server' % proto, 'CSC SHINY %s\t\t' % proto, RunType.runtime,
				arg=HttpRequest(), ex=ShinyUnreachable),
	SysCheckUnit(check_csc_mount, 'csc_mount', 'CSC Shiny File System', 'CSC SHINY FS\t\t', RunType.runtime,
				ex=FileSystemNotMounted),
	SysCheckUnit(check_csc_taito_mount, 'csc_taito_mount', 'CSC Taito File System', 'CSC TAITO FS\t\t', RunType.runtime,
				ex=FileSystemNotMounted),
	SysCheckUnit(check_watcher, 'watcher', 'JobKeeper', 'JOB_KEEPER\t\t', RunType.runtime, ex=WatcherIsNotRunning),
]

from models import ComputeResource, ComputeClass

for each in ComputeResource.objects.all():
	assert isinstance(each, ComputeResource)
	comp = each.comp
	assert isinstance(comp, ComputeClass)
	CHECK_LIST += [comp.conf_check(), comp.online_check()]

CHECK_DICT = dict()
for each_e in CHECK_LIST:
	CHECK_DICT.update({ each_e.url: each_e })


# clem 08/09/2015
def get_template_check_list():
	res = list()
	for each in CHECK_LIST:
		if each.type in [RunType.both, RunType.runtime]:
			# url_prefix = 'status' if not each.lp else 'status_lp'
			res.append(
				{ 'url': '/%s/%s/' % ('status', each.url), 'legend': each.legend, 'id': each.url, 't_out': each.t_out,
				'lp': each.lp }
			)
	return res
