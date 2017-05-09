#!/usr/bin/python
from __future__ import print_function
from subprocess import Popen, PIPE
from distutils.spawn import find_executable
import re


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
	
	def __init__(self):
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
	
	def run(self):
		"""
		run lsof and parse the results into a tmp array that gets passed back to the
		caller.
		"""
		
		tmp = []
		cmd = "%s -PnF0" % self.LSOF_BIN
		p = Popen(cmd.split(' '), stdout=PIPE, close_fds=True)
		for line in p.stdout.xreadlines():
			r2 = dict([(self.flag_cache[x[0:1]], x[1:]) for x in line.rstrip('\n').split('\0')])
			if 'command_name' in r2:
				tmp.append({'info': r2, 'files': []})
			else:
				tmp[-1]['files'].append(r2)
		return tmp


if __name__ == '__main__':
	l = LsOf()
	for r in l.run():
		info = r['info']
		files = r['files']
		
		print("PID(%s) %s" % (info['process_id'], info['command_name']))
		for f in files:
			for k in f:
				print("\t%-20s -> %s" % (k, f[k]))
