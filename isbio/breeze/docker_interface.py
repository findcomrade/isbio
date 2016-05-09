from compute_interface_module import * # has os, abc, function_name
from docker_client import *
from utils import password_from_file, is_from_cli, get_file_md5, get_free_port # , new_thread

__version__ = '0.2'
__author__ = 'clem'
__date__ = '15/03/2016'


# clem 15/03/2016
class DockerInterface(ComputeInterface):
	ssh_tunnel = None
	auto_remove = True
	__docker_storage = None
	_data_storage = None
	_jobs_storage = None
	run_id = '' # stores the md5 of the sent archive ie. the job id
	proc = None
	client = None
	_lock = None
	label = ''
	my_volume = DockerVolume('/home/breeze/data/', '/breeze', 'r')
	my_run = None
	container = None
	cat = DockerEventCategories

	# DOCKER HUB RELATED CONF
	REPO_PWD = password_from_file('~/code/docker_repo')
	REPO_LOGIN = 'fimm'
	REPO_EMAIL = 'clement.fiere@fimm.fi'
	# TARGET DOCKER DAEMON CONF
	DOCKER_REMOTE_HOST = '127.0.0.1'
	DOCKER_REMOTE_PORT = 4243
	DOCKER_LOCAL_PORT = 0
	DOCKER_REMOTE_BIND_ADDR = (DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT)
	DOCKER_LOCAL_BIND_ADDR = None
	DOCKER_REMOTE_DAEMON_URL = 'tcp://%s:%s' % DOCKER_REMOTE_BIND_ADDR
	DOCKER_LOCAL_DAEMON_URL = ''
	# SSH TUNNEL CONFIG
	SSH_HOST = None
	SSH_CMD_BASE = ['ssh', '-CfNnL', '%s:%s:%s' % (DOCKER_LOCAL_PORT, DOCKER_REMOTE_HOST, DOCKER_REMOTE_PORT)]
	SSH_BASH_KILL_BASE = 'ps aux | grep "%s"' + " | awk '{ print $2 }' | tr '\\n' ' '"
	# CONTAINER SPECIFIC
	NORMAL_ENDING = ['Running R script... done !', 'Success !', 'done']

	MY_DOCKER_HUB = DockerRepo(REPO_LOGIN, REPO_PWD, email=REPO_EMAIL)
	LINE3 = '\x1b[34mCreating archive /root/out.tar.xz'
	LINE2 = '\x1b[1mcreate_blob_from_path\x1b[0m(' # FIXME NOT ABSTRACT
	LINES = dict([(-3, LINE3), (-2, LINE2)])

	def __init__(self, compute_target, storage_backend=None):
		"""

		:type storage_backend: module
		"""
		assert isinstance(compute_target, ComputeTarget)

		super(DockerInterface, self).__init__(compute_target, storage_backend)

		self.SSH_HOST = compute_target.tunnel_host
		# TODO changes these to factory
		self.DOCKER_LOCAL_PORT = get_free_port()
		self.DOCKER_LOCAL_BIND_ADDR = ('127.0.0.1', self.DOCKER_LOCAL_PORT)
		self.DOCKER_LOCAL_DAEMON_URL = 'tcp://%s:%s' % self.DOCKER_LOCAL_BIND_ADDR
		self.SSH_CMD = ['ssh', '-CfNnL', '%s:%s:%s' % (self.DOCKER_LOCAL_PORT, self.DOCKER_REMOTE_HOST,
		self.DOCKER_REMOTE_PORT), self.SSH_HOST]
		self.label = compute_target.tunnel_host[0:2]

		res = False
		if not self._test_connection(self.DOCKER_LOCAL_BIND_ADDR):
			self._write_log('No connection to daemon, trying ssh tunnel')
			self._get_ssh()
			if self._test_connection(self.DOCKER_LOCAL_BIND_ADDR):
				res = self._connect()
		else:
			res = self._connect()
		if not res:
			self._write_log('FAILURE connecting to docker daemon, cannot proceed')
			raise DaemonNotConnected

	# TODO externalize
	# clem 08/09/2016
	def _test_connection(self, target):
		import socket
		s = socket.socket() # socket.AF_INET, socket.SOCK_STREAM
		try:
			s.settimeout(2)
			self._write_log('testing connection to %s Tout: %s sec' % (str(target), s.gettimeout()))
			s.connect(target)
			self._write_log('success')
			return True
		except socket.timeout:
			self._write_log('connect %s: Time-out' % str(target))
		except socket.error as e:
			self._write_log('connect %s: %s' % (str(target), e[1]))
		except Exception as e:
			self._write_log('connect %s' % str((type(e), e)))
		finally:
			s.close()

		return False

	# clem 07/04/2016
	def _connect(self):
		self.client = DockerClient(self.DOCKER_LOCAL_DAEMON_URL, self.MY_DOCKER_HUB, False)
		return self._attach_event_manager() and self.client

	# TODO externalize
	# clem 06/04/2016 # FIXME change print to log
	def _get_ssh(self):
		if self.SSH_HOST:
			import subprocess
			print 'Establishing ssh tunnel, running', self._ssh_cmd_list, '...',
			self.ssh_tunnel = subprocess.Popen(self._ssh_cmd_list, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
				preexec_fn=os.setsid)
			print 'done,',
			stat = self.ssh_tunnel.poll()
			while stat is None:
				stat = self.ssh_tunnel.poll()
			print 'bg PID :', self.ssh_tunnel.pid
		else:
			raise AttributeError('Cannot establish ssh tunnel since no ssh_host provided during init')

	def _attach_event_manager(self, run=None):
		if not run and self.my_run:
				run = self.my_run
		if run and isinstance(run, DockerRun):
			run.event_listener = self._event_manager_wrapper()
		return run

	# clem 16/03/2016
	def _write_log(self, txt):
		if str(txt).strip():
			if self.client:
				print '<docker%s>' % ('_' + self.label), txt
				# self.client.write_log_entry(txt)
			else:
				print '<docker%s ?>' % ('_' + self.label), txt

	def _run(self, run):
		self.container = self.client.run(run)
		self._write_log('Got %s' % repr(self.container))

	def _event_manager_wrapper(self):
		def my_event_manager(event):
			assert isinstance(event, DockerEvent)
			# self.write_log(event)
			if event.description == DockerEventCategories.DIE:
				self.job_is_done()
			elif event.description == DockerEventCategories.START:
				self._write_log('%s started' % event.container.name)

		return my_event_manager

	# clem 29/04/2016
	@property
	def _ssh_cmd_list(self):
		assert isinstance(self.SSH_HOST, basestring)
		return self.SSH_CMD

	# clem 20/04/2016
	@property
	def _job_storage(self):
		if not self._jobs_storage:
			self._jobs_storage = self._get_storage(self.storage_backend.jobs_container())
		return self._jobs_storage

	# clem 21/04/2016
	@property
	def _result_storage(self):
		if not self._data_storage:
			self._data_storage = self._get_storage(self.storage_backend.data_container())
		return self._data_storage

	# clem 21/04/2016
	@property
	def _docker_storage(self):
		if not self.__docker_storage:
			self.__docker_storage = self._get_storage(self.storage_backend.management_container())
		return self.__docker_storage

	def send_job(self):
		# FIXME : still on test design (using a pre-assembled report job)
		job_folder = None
		output_filename = None
		if not job_folder:
			job_folder = '/projects/breeze-dev/db/testing/in/'
		if not output_filename:
			output_filename = '/projects/breeze-dev/db/testing/temp.tar.bz2'

		# real implementation
		if self.make_tarfile(output_filename, job_folder):
			self._docker_storage.upload_self() # update the cloud version of azure_storage.py
			self.run_id = get_file_md5(output_filename)
			b = self._job_storage.upload(self.run_id, output_filename)
			if b:
				os.remove(output_filename)
				my_run = DockerRun('fimm/r-light:latest', '/run.sh %s' % self.run_id, self.my_volume)
				# self.my_run = my_run
				self._attach_event_manager(my_run)
				self._run(my_run)
				return True
		else:
			print 'failed'
		return False

	# clem 21/04/2016
	def get_results(self, output_filename=None):
		if not output_filename:
			output_filename = '/projects/breeze-dev/db/testing/results_%s.tar.xz' % self.run_id
		try:
			e = self._result_storage.download(self.run_id, output_filename)

			# if e:
			# 	self.result_storage.erase(self.run_id)
			# TODO extract in original path
			return e
		except self._missing_exception:
			self._write_log('No result found for job %s' % self.run_id)
			raise

	# clem 06/05/2016
	def abort(self):
		self.container.kill()
		self.container.remove_container()

	# clem 06/05/2016
	def busy_waiting(self, *args):
		while self.container.is_running and not self._runnable.aborting:
			time.sleep(1)

	# clem 06/05/2016
	def status(self): # TODO
		return 'unknown'

	# clem 06/05/2016
	def job_is_done(self):
		cont = self.container
		log = str(cont.logs)
		assert isinstance(cont, DockerContainer)
		self._write_log('Died code %s. Total execution time : %s' % (cont.status.ExitCode,
		cont.delta_display))
		if cont.status.ExitCode > 0:
			self._write_log('Failure (container won\'t be deleted) ! Run log :\n%s' % log)
		else:
			self._write_log('Success !')
			# filter the end of the log to match it to a specific pattern, to ensure no unexpected event
			# happened
			the_end = log.split('\n')[-6:-1] # copy the last 5 lines
			for (k, v) in self.LINES.iteritems():
				if the_end[k].startswith(v):
					del the_end[k]
			if the_end != self.NORMAL_ENDING:
				self._write_log('It seems there was some errors, run log :\n%s\nEND OF RUN LOGS !! '
								'##########################' % log)
			if self.auto_remove:
				cont.remove_container()
			self.get_results() #


# clem 04/05/2016
def initiator(compute_target, *args):
	assert isinstance(compute_target, ComputeTarget)
	return DockerInterface(compute_target)


# clem 15/03/2016
class DockerIfTest(DockerInterface): # TEST CLASS
	volumes = {
		'test' : DockerVolume('/home/breeze/data/', '/breeze', 'rw'),
		'final': DockerVolume('/home/breeze/data/', '/breeze', 'rw')
	}
	runs = {
		'op'   : DockerRun('fimm/r-light:op', './run.sh', volumes['test']),
		'rtest': DockerRun('fimm/r-security-blanket:new', './run.sh', volumes['test']),
		'flat' : DockerRun('fimm/r-light:flat', '/breeze/run.sh', volumes['test']),
		'final': DockerRun('fimm/r-light:latest', '/run.sh', volumes['final']),
	}

	def _attach_all_event_manager(self):
		for name, run_object in self.runs.iteritems():
			self.runs[name] = self._attach_event_manager(run_object)
		return True

	# clem 06/04/2016
	def custom_run(self, name=''):
		if not is_from_cli():
			assert name in self.runs.keys()
		if not name:
			self_name = function_name()
			print 'Available run :'
			advanced_pretty_print(self.runs)
			print 'usage:\t%s(RUN_NAME)\ni.e.\t%s(\'%s\')' % (self_name, self_name, self.runs.items()[0][0])
		else:
			run = self.runs.get(name, None)
			if not run:
				self._write_log('No run named "%s", running default one' % name)
			self._run(run)

	def self_test(self): # FIXME Obsolete
		self.test(self.client.get_container, '12')
		self.test(self.client.get_container, '153565748415')
		self.test(self.client.img_run, 'fimm/r-light:op', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:op', '/run.sh')
		self.test(self.client.img_run, 'fimm/r-light:candidate', 'echo "test"')
		self.test(self.client.img_run, 'fimm/r-light:candidate', '/run.sh')
		self.test(self.client.images_list[0].pretty_print)

	def test(self, func, *args): # FIXME Obsolete
		self._write_log('>>%s%s' % (func.im_func.func_name, args))
		return func(*args)
