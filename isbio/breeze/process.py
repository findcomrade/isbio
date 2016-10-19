from multiprocessing import Process as ProcessOriginal
import os
import sys
import itertools
__author__ = 'clem' # fork of python process module

__all__ = ['Process', 'current_process', 'active_children']

try:
	ORIGINAL_DIR = os.path.abspath(os.getcwd())
except OSError:
	ORIGINAL_DIR = None


def current_process():
	'''
	Return process object representing the current process
	'''
	return _current_process


def active_children():
	'''
	Return list of process objects corresponding to live child processes
	'''
	_cleanup()
	return list(_current_process._children)


#
#
#

def _cleanup():
	# check for processes which have finished
	for p in list(_current_process._children):
		
		if hasattr(p, '_popen') and hasattr(p._popen, 'poll') and p._popen.poll() is not None:
			_current_process._children.discard(p)


class MyProcess(ProcessOriginal):
	def _bootstrap(self):
		from multiprocessing import util
		global _current_process

		try:
			self._children = set()
			self._counter = itertools.count(1)
			try:
				# sys.stdin.close()
				sys.stdin = open(os.devnull)
			except (OSError, ValueError):
				pass
			_current_process = self
			util._finalizer_registry.clear()
			util._run_after_forkers()
			util.info('child process calling self.run()')
			try:
				self.run()
				exitcode = 0
			finally:
				pass
				# util._exit_function()
		except SystemExit, e:
			if not e.args:
				exitcode = 1
			elif isinstance(e.args[0], int):
				exitcode = e.args[0]
			else:
				sys.stderr.write(str(e.args[0]) + '\n')
				sys.stderr.flush()
				exitcode = 1
		except:
			exitcode = 1
			import traceback
			sys.stderr.write('Process %s:\n' % self.name)
			sys.stderr.flush()
			traceback.print_exc()

		util.info('process exiting with exitcode %d' % exitcode)
		return exitcode


#
# We subclass bytes to avoid accidental transmission of auth keys over network
#

class AuthenticationString(bytes):
	def __reduce__(self):
		from multiprocessing.forking import Popen
		if not Popen.thread_is_spawning():
			raise TypeError(
				'Pickling an AuthenticationString object is '
				'disallowed for security reasons'
			)
		return AuthenticationString, (bytes(self),)


#
# Create object representing the main process
#

class _MainProcess(MyProcess):
	def __init__(self):
		self._identity = ()
		self._daemonic = False
		self._name = 'MainProcess'
		self._parent_pid = None
		self._popen = None
		self._counter = itertools.count(1)
		self._children = set()
		self._authkey = AuthenticationString(os.urandom(32))
		self._tempdir = None


_current_process = _MainProcess()
del _MainProcess

#
# Give names to some return codes
#

_exitcode_to_name = { }

for name, signum in signal.__dict__.items():
	if name[:3] == 'SIG' and '_' not in name:
		_exitcode_to_name[-signum] = name
		
Process = MyProcess
