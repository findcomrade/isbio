"""

A module that safely import drmaa if it exists
If not drmaa will be set to None

provide job_stat_class as alias to drmaa.JobState and as an replacement class if drmaa does not exists

"""
from threading import Lock
from thread import LockType
from utilz import logger
__version__ = '0.1.1'
__author__ = 'clem'
__date__ = '21/06/2016'

try:
	import drmaa

	job_stat_class = drmaa.JobState
except ImportError as e:
	drmaa = None
	logger.error('importing drmaa: %s' % e)


drmaa_mutex = Lock()
assert isinstance(drmaa_mutex, LockType)
