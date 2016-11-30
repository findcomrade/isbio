import os

SGE_QUEUE_NAME = 'breeze.q' # monitoring only

SGE_MASTER_FILE = '/var/lib/gridengine/default/common/act_qmaster' # FIXME obsolete
SGE_MASTER_IP = '192.168.67.2' # FIXME obsolete
DOTM_SERVER_IP = '128.214.64.5' # FIXME obsolete
RORA_SERVER_IP = '192.168.0.219' # FIXME obsolete
FILE_SERVER_IP = '192.168.0.107' # FIXME obsolete

LEGACY_MONITORING_SGE_QUEUE_NAME = 'breeze.q'
Q_BIN = os.environ.get('Q_BIN', '')
QSTAT_BIN = '%sqstat' % Q_BIN
QDEL_BIN = '%sqdel' % Q_BIN
SGE_QUEUE_NAME = 'breeze.q' # monitoring only
