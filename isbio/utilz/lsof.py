from __future__ import print_function
from subprocess import Popen, PIPE
from distutils.spawn import find_executable
import re
import logging


class LsOf(object):
	"""
	lsof wrapper class

	An automated wrapper around lsof output that yields
	an array of processes with their file handle information
	in the form of:

	results = [
		{
			info: {
				'none': '',
				'user_id': '501',
				'process_id': '22665',
				'process_group_id': '20',
				'parent_pid': '232',
				'login_name': 'nar',
				'command_name': 'mdworker'
			},
			files: [
				...
			]
		},
		...
	]
	"""
	
	LSOF_BIN = find_executable("lsof")
	flagRegex = re.compile(r"\s+(?P<flag>[a-zA-Z])\s+(?P<desc>.*)$")
	flag_cache = {'': 'none'}
	
	def __init__(self, a_file=''):
		"""
		For initialization, we query lsof using the '-Fh?' flag
		to automatically generate a list of possible key names
		so that later on when we're parsing records we can substitute
		them in the final dict.

		When using the -F option, the key names are only provided as
		single characters, which aren't terribly useful if you don't
		know them by heart.
		"""
		
		p = Popen([self.LSOF_BIN, "-F?"], stdout=PIPE, stderr=PIPE, close_fds=True)
		for line in p.stderr.readlines()[1:]:
			m = self.flagRegex.match(line)
			if m is not None:
				flag = m.group('flag')
				desc = m.group('desc').lower()
				for s in (':', ' as', ' ('):
					if desc.find(s) > -1:
						desc = desc[0:desc.find(s)]
						break
				self.flag_cache[flag] = re.sub(r'[/ ,\t_]+', '_', desc)
		self.a_file = a_file
	
	def run(self, _all=False):
		"""
		run lsof and parse the results into a tmp array that gets passed back to the
		caller.
		"""
		
		tmp = []
		cmd = "%s -PnF0%s" % (self.LSOF_BIN, (' ' + self.a_file) if not _all and self.a_file else '')
		logger.info('Popen(%s, stdout=PIPE, close_fds=True)' % cmd.split(' '))
		p = Popen(cmd.split(' '), stdout=PIPE, close_fds=True)
		for line in p.stdout.xreadlines():
			r2 = dict([(self.flag_cache[x[0:1]], x[1:]) for x in line.rstrip('\n').split('\0')])
			if 'command_name' in r2:
				tmp.append({'info': r2, 'files': []})
			else:
				tmp[-1]['files'].append(r2)
		return tmp
	
	# clem 19/04/2017
	def _show_base(self, _all):
		for r in self.run(_all):
			info = r['info']
			files = r['files']
			
			print("PID(%s) %s" % (info['process_id'], info['command_name']))
			for f in files:
				for k in f:
					print("\t%-20s -> %s" % (k, f[k]))
				print('\t' + '-' * 60)
	
	# clem 19/04/2017
	def show_all(self):
		self._show_base(True)
	
	# clem 19/04/2017
	def show_file(self):
		self._show_base(False)
	
	# clem 19/04/2017
	@property
	def proc_count(self):
		return len(self.run())
	
	# clem 19/04/2017
	@property
	def fd_count(self):
		total = 0
		for r in self.run():
			total += len(r['files'])
		return total
	
	# clem 19/04/2017
	@property
	def is_open(self):
		from os import path
		try:
			is_file = self.a_file and path.isfile(self.a_file)
		except Exception:
			is_file = False
		return is_file and self.proc_count > 0
	
	# clem 19/04/2017
	def links_counts_generic(self, access_type):
		count = 0
		if self.is_open:
			for r in self.run():
				files = r['files']
				for f in files:
					if f['access'] == access_type:
						count += 1
		return count
	
	# clem 19/04/2017
	@property
	def read_links_counts(self):
		return self.links_counts_generic('r')
	
	# clem 19/04/2017
	@property
	def write_links_counts(self):
		return self.links_counts_generic('w')
	
	# clem 19/04/2017
	@property
	def has_read(self):
		return self.read_links_counts > 0
	
	# clem 19/04/2017
	@property
	def has_writes(self):
		return self.write_links_counts > 0
	
	# clem 19/04/2017
	def show_info(self):
		print('is_open: %s, proc_count: %s, fd_count: %s, ' % (self.is_open, self.proc_count, self.fd_count))
		print('read: %s, writes: %s' % (self.read_links_counts, self.write_links_counts))
	

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(ch)


def test_ls():
	file_path = '/homes/breeze/test1'
	l = LsOf(file_path)
	a = open(file_path)
	with open(file_path, 'w'):
		l.show_file()
		l.show_info()
	l.show_file()
	l.show_info()
	a.close()
	l.show_info()
	
	LsOf().show_info()


def test_jpype():
	import jpype
	import os.path
	
	jarpath = '/homes/breeze/code/venv/lib' # os.path.join(os.path.abspath("."), "lib")
	# print("-Djava.ext.dirs=%s" % jarpath)
	# jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.ext.dirs=%s" % jarpath)
	jpype.startJVM(jpype.getDefaultJVMPath(), '"-jar /homes/breeze/code/venv/lib/aspose-cells-17.4.0.jar"')
	jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=%s" % jarpath)
	jpype.java.lang.System.out.println("hello world")
	
	document = jpype.JClass("com.aspose.cells.cells")
	# document = jpype.JClass("com.aspose.words.Document")
	
	doc = document()
	
	print(doc, repr(doc))
	
	# jpype.startJVM(jpype.getDefaultJVMPath(), '"-Xmx512M -Xms256M"')
	# jpype.startJVM(jpype.getDefaultJVMPath(), '"-jar /homes/breeze/code/venv/lib/aspose-cells-17.4.0.jar"')


if __name__ == '__main__':
	# test_ls()
	test_jpype()
