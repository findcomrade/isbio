from __builtin__ import property
from django.template.defaultfilters import slugify
from django.db.models.fields.related import ForeignKey
from django.contrib.auth.models import User # as DjangoUser
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpRequest
from breeze import managers, utils, system_check, comp
from comp import Trans
from utils import *
from django.db import models
import importlib
import copy
from non_db_objects import *

if settings.HOST_NAME.startswith('breeze'):
	import drmaa

system_check.db_conn.inline_check()

CATEGORY_OPT = (
	(u'general', u'General'),
	(u'visualization', u'Visualization'),
	(u'screening', u'Screening'),
	(u'sequencing', u'Sequencing'),
)

# TODO : move all the logic into objects here
drmaa_lock = Lock()
sge_lock = Lock()


JOB_PS = JobStat.job_ps # legacy


# clem 20/06/2016
class CustomModelAbstract(models.Model):
	""" Provides and enforce read-only property ( read_only ). This property is set by the CustomManager """

	__prop_read_only = False

	@property
	def read_only(self):
		""" Tells if the object read only (in a DataBase sense).

		If RO, any changes can be made to the object (except changing the RO property),
		but keep in mind that there will be no effect on the DataBse.

		:return: if model object is read-only or not
		:rtype: bool
		"""
		return self.__prop_read_only

	@read_only.setter
	def read_only(self, val):
		""" Switch the object to read-only mode (in a DataBase sense).

		Once set to True, this cannot be changed back, and any change to the object WONT be saved to DB.

		:param val: only accepts True
		:type val: bool
		:raise:  ReadOnlyAttribute
		"""
		if not self.__prop_read_only and val:
			self.__prop_read_only = True
		else:
			raise ReadOnlyAttribute

	def save(self, force_insert=False, force_update=False, using=None):
		if not self.read_only:
			return super(CustomModelAbstract, self).save(force_insert, force_update, using)
		return False

	def delete(self, using=None):
		if not self.read_only:
			return super(CustomModelAbstract, self).delete(using)
		return False

	class Meta:
		abstract = True


class Institute(CustomModelAbstract):
	institute = models.CharField(max_length=75, default='FIMM')

	def __unicode__(self):
		return self.institute

	# clem 20/06/2016
	@property
	def default(self):
		return self.objects.get_or_create({ 'id': 1, 'institute': 'FIMM' })


# clem 20/06/2016
class CustomModel(CustomModelAbstract):
	"""
	Provides several specific features :
		_ custom object Manager

		_ institute field, that is mandatory for all db objects
	"""
	objects = managers.CustomManager()

	institute = ForeignKey(Institute, default=Institute.default)
	""" Store the institute which own this object, to efficiently segregate data """

	class Meta:
		abstract = True


# 04/06/2015
class OrderedUser(User):
	class Meta:
		ordering = ["username"]
		proxy = True


# TODO add an Institute db field
# TODO change to CustomModel
class Post(CustomModelAbstract):
	author = ForeignKey(User)
	title = models.CharField(max_length=150)
	body = models.TextField(max_length=3500)
	time = models.DateTimeField(auto_now_add=True)
	
	def __unicode__(self):
		return self.title


class Project(CustomModel):
	name = models.CharField(max_length=50, unique=True)
	manager = models.CharField(max_length=50)
	pi = models.CharField(max_length=50)
	author = ForeignKey(User)

	collaborative = models.BooleanField(default=False)
	
	wbs = models.CharField(max_length=50, blank=True)
	external_id = models.CharField(max_length=50, blank=True)
	description = models.CharField(max_length=1100, blank=True)

	objects = managers.ProjectManager() # Custom manage 19/04/2016

	def __unicode__(self):
		return self.name


# TODO add an Institute db field
# TODO change to CustomModel
class Group(CustomModelAbstract):
	name = models.CharField(max_length=50, unique=True)
	author = ForeignKey(User)
	team = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='group_content')

	def delete(self, _=None):
		if not self.read_only:
			self.team.clear()

	def __unicode__(self):
		return self.name


def shiny_header():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_HEADER_FILE_NAME))
	return str(fileh.read())


# 17/06/2015
def shiny_loader():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_LOADER_FILE_NAME))
	return str(fileh.read())


# 17/06/2015
def shiny_files():
	fileh = open(str(settings.SHINY_REPORT_TEMPLATE_PATH + settings.SHINY_FILE_LIST))
	return str(fileh.read())


# 08/06/2015
# TODO change from CustomModel to CustomModelAbstract
# TODO change the institute field to a ManyToManyField
class ShinyReport(CustomModel):
	FILE_UI_NAME = settings.SHINY_UI_FILE_NAME
	FILE_SERVER_NAME = settings.SHINY_SERVER_FILE_NAME
	# FILE_DASH_UI = settings.SHINY_DASH_UI_FN
	# FILE_DASH_SERVER = settings.SHINY_DASH_SERVER_FN
	FILE_HEADER_NAME = settings.SHINY_HEADER_FILE_NAME
	FILE_GLOBAL = settings.SHINY_GLOBAL_FILE_NAME
	FILE_LIST = settings.SHINY_FILE_LIST
	# FILE_LOADER = settings.SHINY_LOADER_FILE_NAME
	# SERVER_FOLDER = settings.SHINY_SERVER_FOLDER
	# UI_FOLDER = settings.SHINY_UI_FOLDER
	RES_FOLDER = settings.SHINY_RES_FOLDER
	SHINY_REPORTS = settings.SHINY_REPORTS
	REPORT_TEMPLATE_PATH = settings.SHINY_REPORT_TEMPLATE_PATH
	SYSTEM_FILE_LIST = [FILE_UI_NAME, FILE_SERVER_NAME, FILE_GLOBAL, FILE_HEADER_NAME, RES_FOLDER, RES_FOLDER[:-1]]
	# FS_ACL = 0775
	FS_ACL = ACL.RWX_RX_
	FS_REMOTE_ACL = ACL.RWX_RX_

	title = models.CharField(max_length=55, unique=True, blank=False, help_text="Choose a title for this Shiny Report")
	description = models.CharField(max_length=350, blank=True, help_text="Optional description text")
	author = ForeignKey(User)
	created = models.DateTimeField(auto_now_add=True)

	objects = managers.ObjectsWithAuth()
	# institute = ForeignKey(Institute, default=Institute.default)

	custom_header = models.TextField(blank=True, default=shiny_header(),
		help_text="Use R Shiny code here to customize the header of the dashboard<br />"
				  "Here is a basic example of what you can do.<br />\n"
				  "For more information, please refer to Shiny documentation.")

	custom_loader = models.TextField(blank=True, default=shiny_loader(),
		help_text="Use R Shiny code here to customize the global server part of the "
				  "dashboard<br />This is usefull to load files, or declare variables "
				  "that will be accessible to each attached tags:<br />NB : you may "
				  "reference, in the next field, every file you use here. Use a $ to "
				  "reference your file according to the 'tname' you associated with it.")

	custom_files = models.TextField(blank=True, default=shiny_files(),
		help_text="Use the following JSON format to reference your files<br />This "
				  "enables Breeze to dynamically check for the files you marked as "
				  "required.<br />")

	enabled = models.BooleanField(default=True)

	@property
	def get_name(self):
		return slugify(str(self.title))

	@property
	def __folder_path_remote(self):
		return str('%s%s/app/' % (settings.SHINY_REMOTE_REPORTS_INTERNAL, self.get_name))

	def __folder_path_base_gen(self, remote=False):
		return str('%s%s/' % (self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self.get_name))

	@property
	def _folder_path_base(self):
		return self.__folder_path_base_gen()

	def __folder_path_gen(self, remote=False):
		return str('%sapp/' % self.__folder_path_base_gen(remote))

	@property
	def folder_path(self):
		return self.__folder_path_gen()

	def server_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_SERVER_NAME))

	def ui_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_UI_NAME))

	def global_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.FILE_GLOBAL))

	def res_folder_path(self, remote=False):
		return str('%s%s' % (self.__folder_path_gen(remote), self.RES_FOLDER))

	# path_template_folder = REPORT_TEMPLATE_PATH
	path_server_r_template = REPORT_TEMPLATE_PATH + FILE_SERVER_NAME
	path_ui_r_template = REPORT_TEMPLATE_PATH + FILE_UI_NAME
	path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL

	# path_heade_r_template = REPORT_TEMPLATE_PATH + FILE_HEADER_NAME
	# path_global_r_template = REPORT_TEMPLATE_PATH + FILE_GLOBAL
	# path_loader_r_template = str(REPORT_TEMPLATE_PATH + FILE_LOADER)
	# path_file_lst_template = str(REPORT_TEMPLATE_PATH + FILE_LIST)
	# path_dash_ui_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_UI
	# path_dash_server_r_template = REPORT_TEMPLATE_PATH + FILE_DASH_SERVER

	# TODO rework the next 3 functions
	@property
	def shiny_mode(self):
		if self.shiny_remote_ok:
			return 'remote'
		elif self.shiny_local_ok:
			return 'local'

	@property
	def shiny_remote_ok(self):
		return settings.SHINY_REMOTE_ENABLE and settings.SHINY_MODE == 'remote'

	@property
	def shiny_local_ok(self):
		return settings.SHINY_LOCAL_ENABLE and settings.SHINY_MODE == 'local'

	def url(self, report, force_remote=False, force_local=False):
		assert isinstance(report, Report)
		if force_remote or self.shiny_remote_ok and not force_local:
			return '%s%s/' % (settings.SHINY_TARGET_URL, report.shiny_key)
		elif self.shiny_local_ok:
			from django.core.urlresolvers import reverse
			from views import report_shiny_in_wrapper
			return reverse(report_shiny_in_wrapper, kwargs={ 'rid': report.id })

	@property # relative path to link holder directory
	def _link_holder_rel_path(self):
		# the point of this property, is that you can change the folder structure by only changing this
		return '%s/lnk' % self.get_name

	def _link_holder_path(self, remote=False): # full path to lnk holder directory
		return '%s%s/' % (
		self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self._link_holder_rel_path)

	def report_link_rel_path(self, data):
		"""
		Return the path to the symlink file to the actual report WITHOUT a trailing /
		:param data: a valid Report id
		:return: path to the symlink file to the actual report WITHOUT a trailing /
		:rtype: str
		"""
		return '%s/%s' % (self._link_holder_rel_path, data)

	def report_link(self, data, rel=False, remote=False):
		if rel:
			return self.report_link_rel_path(data)
		return '%s%s' % (
		self.SHINY_REPORTS if not remote else settings.SHINY_REMOTE_REPORTS, self.report_link_rel_path(data))

	# Clem 22/09/2015
	@staticmethod
	def check_csc_mount():
		from system_check import check_csc_mount
		return check_csc_mount()

	# Clem 05/10/2015
	@staticmethod
	def remote_shiny_ready():
		return settings.SHINY_REMOTE_ENABLE and ShinyReport.check_csc_mount()

	# Clem 23/09/2015
	@property # may be dynamic in the future and return if this very report should go to remote Shiny
	def make_remote_too(self):
		"""
		If remote Shiny report should be generated, if SHINY_REMOTE_ENABLE and CSC FS is mounted
		:return:
		:rtype:
		"""
		return self.remote_shiny_ready()

	def update_folder(self):
		"""
		Creates the directory structure, removing any previously existing content,
		creates sever and ui sub-folders and link server and ui dashboard 'tag'
		Handles both local and remote Shiny
		"""
		# import os.path
		from os import mkdir

		if settings.SHINY_LOCAL_ENABLE:
			safe_rm(self._folder_path_base, ignore_errors=True)
			mkdir(self._folder_path_base, self.FS_ACL)
			mkdir(self._link_holder_path(), self.FS_ACL)
			mkdir(self.folder_path, self.FS_ACL)
			mkdir('%s%s/' % (self.folder_path, self.RES_FOLDER), self.FS_ACL)

		if self.make_remote_too:
			safe_rm(self.__folder_path_base_gen(True), ignore_errors=True)
			mkdir(self.__folder_path_base_gen(True), self.FS_REMOTE_ACL)
			mkdir(self.report_link('', remote=True), self.FS_REMOTE_ACL)
			mkdir(self.__folder_path_gen(True), self.FS_REMOTE_ACL)
			mkdir('%s%s/' % (self.__folder_path_gen(True), self.RES_FOLDER), self.FS_REMOTE_ACL)

	def _link_all_reports(self, force=False):
		"""
		Triggers the linking of each Reports that exists of every attached ReportType
		Handle both local and remote Shiny
		:param force: force linking of each Reports, even if files are missing, or the link already existent
		:type force: bool
		"""
		has_remote = self.make_remote_too
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.f.get_done(False, False).filter(type=rtype):
					if True: # report.is_r_successful:
						self.link_report(report, force, has_remote)

	# Clem 24/09/2015
	def _remote_ignore_wrapper(self, report):
		"""
		return the remote_ignore with specific report context to be called by copythree
		:type report: Report
		:rtype: callable()
		"""
		assert isinstance(report, Report)

		def remote_ignore(_, names):
			"""
			:type names: str
			:rtype: list
			Return a list of files to ignores amongst names
			"""
			import fnmatch
			ignore_list = self.SYSTEM_FILE_LIST + report.hidden_files
			out = list()
			for each in names:
				# if each in ignore_list or each[:-1] == '~' or fnmatch.fnmatch():
				if each[:-1] == '~':
					out.append(each)
				else:
					for ignore in ignore_list:
						if fnmatch.fnmatch(each, ignore):
							out.append(each)
							break
			return out

		return remote_ignore

	def link_report(self, report, force=False, remote_too=False):
		"""
		Link a standard report to this ShinyReport using soft-links. (updates or creates linking)
		If the ShinyReport skeleton has previously been generated,
			this step is enough to enable a report to be visualized through Shiny
		Handle both local and remote Shiny (with remote_too = True)
		:param report: a valid Report instance
		:type report: Report
		:param force: force linking even if files are missing, or the link already existent
		:type force: bool
		"""
		log_obj = get_logger()
		log_obj.debug(
			"updating shinyReport %s-%s slink for report %s %s" % (
			self.get_name, self.id, report.id, 'FORCING' if force else ''))

		from os.path import isdir, isfile, islink
		from os import listdir, access, R_OK # , mkdir

		assert isinstance(report, Report)
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report.id)
		report_remote_link = self.report_link(report.shiny_key, remote=True) if remote_too else ''
		# if the home folder of the report exists, and the link doesn't yet
		if isdir(report_home[:-1]) and report_home != settings.MEDIA_ROOT:
			# check that the report has all required files
			if not force:
				j = self.related_files()
				for each in j: # for every required registered file
					path = '%s%s' % (report_home, each['path'])
					if each['required'] and not (isfile(path) and access(path, R_OK)):
						log_obj.warning("%s missing required file %s" % (report.id, path))
						return
			# LOCAL make of soft-link for each files/folder of the shinyReport folder into the Report folder
			if settings.SHINY_LOCAL_ENABLE and (force or not islink(report_link)):
				for item in listdir(self.folder_path): # TODO should be recursive ?
					auto_symlink('%s%s' % (self.folder_path, item), '%s%s' % (report_home, item))
				# Creates a slink in shinyReports to the actual report
				auto_symlink(report_home, report_link)
			# REMOTE make of soft-link for each files/folder of the shinyReport folder into the Report folder
			if remote_too and (force or not islink(report_remote_link)):
				# del the remote report copy folder
				safe_rm(report.remote_shiny_path, ignore_errors=True)
				try:
					# copy the data content of the report
					safe_copytree(report.home_folder_full_path, report.remote_shiny_path,
						ignore=self._remote_ignore_wrapper(report))
				except Exception as e:
					log_obj.warning("%s ShinyReport copy error %s" % (report.id, e))

				# link ShinyReport files
				for item in listdir(self.folder_path): # TODO should be recursive ?
					# remove_file_safe('%s%s' % (report.remote_shiny_path, item))
					auto_symlink('%s%s' % (self.__folder_path_remote, item), '%s%s' % (report.remote_shiny_path, item))

				# Creates a slink in shinyReports to the actual report
				auto_symlink(report.remote_shiny_path, report_remote_link)
		else: # the target report is missing we remove the link
			self.unlink_report(report)

	# TODO upgrade to remote shiny
	def unlink_report(self, report, remote=False):
		"""
		Do the opposite of link_report, useful if a specific Report has been individually deleted
		:param report: a valid Report instance
		:type report: Report
		"""
		assert isinstance(report, Report)
		import os
		# handles individually each generated report of this type
		report_home = report.home_folder_full_path
		report_link = self.report_link(report.id)

		# if the home folder of the report exists, and the link doesn't yet
		if os.path.isdir(report_home) and report_home != settings.MEDIA_ROOT:
			# removes the soft-link for each files/folder of the shinyReport folder into the Report folder
			for item in os.listdir(self.folder_path):
				remove_file_safe('%s%s' % (report_home, item)) # TODO check
		if os.path.islink(report_link):
			# removes the slink in shinyReports to the actual report
			remove_file_safe(report_link) # unlink from shiny TODO check

	# TODO upgrade to remote shiny
	def _unlink_all_reports(self, remote=False):
		"""
		Do the opposite of _link_all_reports , usefull if a this ShinyReport has been delete, or unlink from a ReportType
		Triggers the unlinking of each Reports that exists of every attached ReportType
		"""
		if ReportType.objects.filter(shiny_report=self).count() > 0: # if attached to any Report
			for rtype in ReportType.objects.filter(shiny_report=self):
				for report in Report.objects.filter(type=rtype):
					self.unlink_report(report, remote)

	def import_tag_res(self, tag):
		"""
		Import every resources ( www folder) of a specific tag
		:param tag: a valid ShinyTag instance
		:type tag: ShinyTag
		"""
		from distutils.dir_util import copy_tree

		assert isinstance(tag, ShinyTag)
		copy_tree(tag.path_res_folder, self.res_folder_path()) # TODO replace with symlimks ?
		if self.make_remote_too:
			copy_tree(tag.path_res_folder, self.res_folder_path(True)) # TODO replace with symlimks ?

	def related_files(self, formatted=False):
		"""
		Returns a list of related files for the report
		:rtype: dict or list
		"""
		# fixed on 11/09/2015
		# fixed on 18/12/2015
		# TODO check expected behavior regarding templates
		j = list()
		if self.custom_files is not None and self.custom_files != '':
			import json
			log_obj = get_logger()

			try:
				# jfile = open(ShinyReport.path_file_lst_template)
				# j = json.load(jfile)
				j = json.loads(self.custom_files)
			# jfile.close()
			except ValueError as e:
				log_obj.exception(e.message)
			# raise ValueError(e)
			if formatted:
				d = dict()
				for each in j:
					d.update({ each['tname']: each['path'] })
				return d
		return j

	# TODO expired design
	def get_parsed_loader(self):
		from string import Template

		# file_loaders = open(ShinyReport.path_loader_r_template)
		# src = Template(file_loaders.read())
		if self.custom_loader is not None and self.custom_loader != '':
			src = Template(self.custom_loader)
			# file_loaders.close()
			# return src.safe_substitute(ShinyReport.related_files(formatted=True))
			return src.safe_substitute(self.related_files(formatted=True))

	def generate_server(self, a_user=None, remote=False): # generate the report server.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n  '

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens server.R template file
		filein = open(self.path_server_r_template)
		src = Template(filein.read())
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					# add it to the source list
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP,
						each.path_dashboard_server(remote)))
				else:
					alist.append('### DISABLED Tag %s by %s (%s) %s' % (
						each.name, each.author.get_full_name(), each.author, each.created))
		loaders = self.get_parsed_loader() # TODO redo
		alist.append('') # avoid join errors if list is empty
		d = {
			'title'    : self.title,
			'generated': generated,
			'updated'  : updated,
			'loaders'  : loaders,
			'sources'  : SEP.join(alist)
		}
		assert (isinstance(src, Template))
		result = src.safe_substitute(d)
		f = open(self.server_path(remote), 'w')
		f.write(result)
		f.close()
		return

	def generate_ui(self, a_user=None, remote=False):  # generate the report ui.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n'
		SEP2 = ',\n  '

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens ui.R template file
		filein = open(self.path_ui_r_template)
		src = Template(filein.read())
		filein.close()
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		tag_vars = list()
		menu_list = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				if each.enabled:
					self.import_tag_res(each)
					alist.append('### Tag %s by %s (%s) %s%ssource("%s",local = TRUE)' % (
						each.name, each.author.get_full_name(), each.author, each.created, SEP,
						each.path_dashboard_body(remote)))
					tag_vars.append(each.get_name.upper())
					menu_list.append(each.menu_entry)
				else:
					alist.append('### DISABLED Tag %s by %s (%s) %s' % (
						each.name, each.author.get_full_name(), each.author, each.created))
		alist.append('')
		menu_list.append('')
		d = {
			'title'     : self.title,
			'header'    : self.custom_header,
			'generated' : generated,
			'updated'   : updated,
			'menu_items': SEP2.join(menu_list),
			'sources'   : SEP.join(alist),
			'tag_vars'  : SEP2.join(tag_vars),
		}
		# do the substitution
		result = src.substitute(d)
		f = open(self.ui_path(remote), 'w')
		f.write(result)
		f.close()
		return

	def generate_global(self, a_user=None, remote=False):  # generate the report ui.R file to include all the tags
		"""
		Handle either LOCAL or REMOTE at once
		:param a_user:
		:type a_user:
		:param remote:
		:type remote:
		:return:
		:rtype:
		"""
		from string import Template
		import auxiliary as aux

		SEP = '\n'

		if a_user is None or not isinstance(a_user, (User, OrderedUser)):
			a_user = self.author
		# opens ui.R template file
		filein = open(self.path_global_r_template)
		src = Template(filein.read())
		# document data
		generated = 'Generated on %s for user %s (%s)' % (self.created, self.author.get_full_name(), self.author)
		updated = 'Last updated on %s for user %s (%s)' % (aux.date_t(), a_user.get_full_name(), a_user)
		alist = list()
		if ShinyTag.objects.filter(attached_report=self).count() > 0:
			for each in self.shinytag_set.all().order_by('order'):
				# base, ui_path, _ = self.get_tag_path(each)
				file_glob = open(each.folder_name + self.FILE_GLOBAL)
				alist.append('### from tag %s by %s (%s) %s\n%s' % (
					each.name, each.author.get_full_name(), each.author, each.created, file_glob.read()))
				file_glob.close()
		alist.append('')
		d = {
			'generated' : generated,
			'updated'   : updated,
			'tag_global': SEP.join(alist)
		}
		# do the substitution
		result = src.substitute(d)
		f = open(self.global_path(remote), 'w')
		f.write(result)
		f.close()
		return

	# TODO implement a lock mechanism for concurrency safety
	def regen_report(self, a_user=None):
		"""
		Handle BOTH local and remote Shiny at Once
		:param a_user:
		:type a_user:
		:return:
		:rtype:
		"""
		log_obj = get_logger()
		log_obj.info("rebuilding shinyReport %s-%s for user %s" % (self.id, self.get_name, a_user))
		self.update_folder()
		# local : TODO should generate disregarding of local shiny status ?
		if settings.SHINY_LOCAL_ENABLE:
			log_obj.debug("rebuilding LOCAL on shinyReport %s-%s" % (self.id, self.get_name))
			self.generate_server(a_user)
			self.generate_ui(a_user)
			self.generate_global(a_user)
		# remote
		if self.make_remote_too:
			log_obj.debug("rebuilding REMOTE on shinyReport %s-%s" % (self.id, self.get_name))
			self.generate_server(a_user, True)
			self.generate_ui(a_user, True)
			self.generate_global(a_user, True)
		log_obj.debug("re-linking and eventual remote copy on shinyReport %s-%s" % (self.id, self.get_name))
		self._link_all_reports()

	def clean(self):
		pass

	def save(self, *args, **kwargs):
		super(ShinyReport, self).save(*args, **kwargs) # Call the "real" save() method.
		self.regen_report()

	def delete(self, using=None):
		import shutil

		log_obj = get_logger()
		log_obj.info("deleted shinyReport %s : %s" % (self.id, self))
		# unlinking all attached Reports
		self._unlink_all_reports()
		# Deleting the folder
		shutil.rmtree(self._folder_path_base, ignore_errors=True)
		if self.make_remote_too:
			log_obj.info("deleted remote shinyReport %s : %s" % (self.id, self))
			self._unlink_all_reports(True)
			shutil.rmtree(self.__folder_path_base_gen(True), ignore_errors=True)
		super(ShinyReport, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('created',)

	def __unicode__(self):
		return self.get_name


# clem 13/05/2016
# TODO change from CustomModel to CustomModelAbstract
# TODO change the institute field to a ManyToManyField
class ExecConfig(ConfigObject, CustomModel):
	"""
	Defines and describes every shared attributes/methods of exec resource abstract classes.
	"""
	name = models.CharField(max_length=32, blank=False, help_text="Name of this exec resource")
	label = models.CharField(max_length=64, blank=False, help_text="Label text to be used in the UI")
	# institute = ForeignKey(Institute, default=Institute.default)

	def file_name(self, filename):
		return super(ExecConfig, self).file_name(filename)

	config_file = models.FileField(upload_to=file_name, blank=False, db_column='config',
		help_text="The config file for this exec resource")
	enabled = models.BooleanField(default=True, help_text="Un-check to disable target")

	CONFIG_EXEC_SYSTEM = 'system'
	CONFIG_EXEC_VERSION = 'version'
	CONFIG_EXEC_BIN = 'bin'
	CONFIG_EXEC_FILE_IN = 'file_in'
	CONFIG_EXEC_FILE_OUT = 'file_out'
	CONFIG_EXEC_ARGS = 'args'
	CONFIG_EXEC_RUN = 'run'
	CONFIG_EXEC_ARCH_CMD = 'arch_cmd'
	CONFIG_EXEC_VERSION_CMD = 'version_cmd'

	@property
	def folder_name(self):
		"""

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return settings.EXEC_CONFIG_FN

	@property
	def exec_config(self):
		return self.config.items(self.CONFIG_GENERAL_SECTION)

	@property
	def exec_system(self):
		""" the name of sub system to use to run the job (currently useless)

		for example :
		R2
		python3

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_SYSTEM)

	@property
	def exec_version(self):
		""" the supposed version of the used system, for information purposes

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_VERSION)

	@property
	def exec_bin_path(self):
		""" the path or name of the system to use to run the job,

		for example if you are using R or python this would be the path of R or python binary.
		if you are using docker, this would be the name of the container,
		etc.

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_BIN)

	@property
	def exec_file_in(self):
		""" the file name containing the source code to run as the job

		example : script.r or job.py

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_FILE_IN)

	@property
	def exec_file_out(self):
		""" the file name to which save the output (log)

		example : script.r.Rout or job.py.log

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_FILE_OUT)

	@property
	def exec_args(self):
		""" the arguments to be passed to the binary

		example : CMD BATCH --no-save

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_ARGS)

	@property
	def exec_run(self):
		""" the command string, including the file name to be passed to the binary (usually %(args)s %(file)s)

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_RUN)

	# clem 14/05/2016
	@property
	def exec_arch_cmd(self):
		""" a full command line to obtain the architecture against which the exec sub-system has been built for

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_ARCH_CMD)

	# clem 14/05/2016
	@property
	def exec_version_cmd(self):
		"""  a full command line to obtain the version of the exec sub-system

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC_VERSION_CMD)

	class Meta(ConfigObject.Meta):
		abstract = False
		db_table = 'breeze_execconfig'


# clem 13/05/2016
# TODO change from CustomModel to CustomModelAbstract
# TODO change the institute field to a ManyToManyField
class EngineConfig(ConfigObject, CustomModel):
	""" Defines and describes every shared attributes/methods of exec resource abstract classes. """
	name = models.CharField(max_length=32, blank=False, help_text="Name of this engine resource")
	label = models.CharField(max_length=64, blank=False, help_text="Label text to be used in the UI")
	# institute = ForeignKey(Institute, default=Institute.default)

	def file_name(self, filename):
		return super(EngineConfig, self).file_name(filename)

	config_file = models.FileField(upload_to=file_name, blank=False, db_column='config',
		help_text="The config file for this engine resource")
	enabled = models.BooleanField(default=True, help_text="Un-check to disable target")

	@property
	def folder_name(self):
		"""

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return settings.ENGINE_CONFIG_FN

	@property
	def engine_config(self):
		return self.config.items(self.CONFIG_GENERAL_SECTION)

	class Meta(ConfigObject.Meta):
		abstract = False
		db_table = 'breeze_engineconfig'


# 19/04/2016
# TODO change from CustomModel to CustomModelAbstract
# TODO change the institute field to a ManyToManyField
class ComputeTarget(ConfigObject, CustomModel):
	""" Defines and describes every shared attributes/methods of computing resource abstract classes.
	"""
	name = models.CharField(max_length=32, blank=False, help_text="Name of this Compute resource target")
	label = models.CharField(max_length=64, blank=False, help_text="Label text to be used in the UI")
	# institute = ForeignKey(Institute, default=Institute.default)

	def file_name(self, filename):
		return super(ComputeTarget, self).file_name(filename)

	config_file = models.FileField(upload_to=file_name, blank=False, db_column='config',
		help_text="The config file for this target")
	enabled = models.BooleanField(default=True, help_text="Un-check to disable target")

	_storage_module = None
	_compute_module = None
	__compute_interface = None
	__exec = None
	__engine = None
	_runnable = None
	CONFIG_TYPE = 'type'
	CONFIG_TUNNEL = 'tunnel'
	CONFIG_ENGINE = 'engine'
	CONFIG_STORAGE = 'storage'
	CONFIG_EXEC = 'exec'

	CONFIG_TUNNEL_HOST = 'host'
	CONFIG_TUNNEL_USER = 'user'
	CONFIG_TUNNEL_PORT = 'port'

	@property
	def folder_name(self):
		"""

		:return: the generated name of the folder to be used to store content of instance
		:rtype: str
		"""
		return settings.TARGET_CONFIG_FN

	# clem 26/05/2016
	@property
	def is_operational(self):
		""" Is this object is ready to be used, i.e. all its dependencies are available, enabled and ready

		:return: If this ComputeTarget is enabled, and all its dependencies are enabled (i.e. exec_obj and engine_obj)
		:rtype: bool
		"""
		return self.enabled and self.exec_obj.enabled and self.engine_obj.enabled

	# clem 26/05/2016
	@property
	def as_tuple(self):
		""" The tuple object that can be used in a list to construct a Form <select> list.

		:return:
		:rtype: tuple[int, str]
		"""
		return tuple((self.id, self.label))

	def __init__(self, *args, **kwargs):
		super(ComputeTarget, self).__init__(*args, **kwargs)

	@property
	def target_type(self):
		""" the type of target : local|remote

		:rtype: list
		"""
		return self.get(self.CONFIG_TYPE)

	#
	# TUNNEL CONFIG
	#

	@property
	def target_tunnel(self):
		""" the name of the tunnel system to use (usually ssh), or 'no' if not using tunneling.
		A config section with the same name must be present if the value is different from no

		:rtype: str
		"""
		return self.get(self.CONFIG_TUNNEL)

	@property
	def target_use_tunnel(self):
		""" if this target uses a tunnel

		:rtype: bool
		"""
		return self.target_tunnel != 'no'

	@property
	def target_tunnel_conf(self):
		""" the whole configuration of the [tunnel_name] section, if present (optional)

		:rtype: list
		"""
		if self.target_use_tunnel:
			return self.config.items(self.target_tunnel)
		return list()

	# clem 04/05/2016
	@property
	def tunnel_host(self):
		""" the FQDN or ip address of the target to connect to using tunneling (if using tunneling, '' otherwise)

		:rtype: str
		"""
		if self.target_use_tunnel:
			return self.get(self.CONFIG_TUNNEL_HOST, self.target_tunnel)
		return ''

	# clem 04/05/2016
	@property
	def tunnel_user(self):
		""" the username to use to connect to the tunneling target (if using tunneling, '' otherwise)

		:rtype: str
		"""
		if self.target_use_tunnel:
			return self.get(self.CONFIG_TUNNEL_USER, self.target_tunnel)
		return ''

	# clem 04/05/2016
	@property
	def tunnel_port(self):
		""" the port number to use to connect to the tunneling target (if using tunneling, '' otherwise)

		:rtype: str
		"""
		if self.target_use_tunnel:
			return self.get(self.CONFIG_TUNNEL_PORT, self.target_tunnel)
		return ''

	#
	# ENGINE
	#

	@property
	def target_engine_name(self):
		""" the name of the engine to use, a config section with the same name MUST be present, along with a python
		module named [engine_name]_interface.py

		:rtype: str
		"""
		return self.get(self.CONFIG_ENGINE)

	# clem 16/05/2016
	@property
	def engine_section(self):
		return self.config.items(self.target_engine_name)

	# clem 13/05/2016
	@property
	def engine_obj(self): # as override
		""" the __engine object related to this target, as defined in this config file

		:rtype: EngineConfig
		"""
		if not self.__engine:
			self.__engine = EngineConfig.objects.get(name=self.target_engine_name)
		return self.__engine

	#
	# EXEC
	#

	# clem 13/05/2016
	@property
	def target_exec_name(self):
		""" the name of the config section to use to configure the execution

		:rtype: str
		"""
		return self.get(self.CONFIG_EXEC)

	# clem 13/05/2016
	@property
	def exec_obj(self): # as override
		""" the ExecConfig object related to this target, as defined in this config file

		:rtype: ExecConfig
		"""
		if not self.__exec:
			self.__exec = ExecConfig.objects.get(name=self.target_exec_name)
		return self.__exec

	#
	# ACCESS TO MODULES / INTERFACES / RUNNABLE CLIENT OBJECT
	#

	#
	# STORAGE
	#

	# clem 04/05/2016
	@property
	def target_storage_engine(self):
		""" the name of the storage engine, matching a python module

		:rtype: str
		"""
		return self.get(self.CONFIG_STORAGE)

	# clem 04/05/2016
	@property
	def storage_module(self):
		""" The python module used as the storage interface for this target

		:rtype: module
		"""
		if not self._storage_module:
			try:
				self._storage_module = importlib.import_module('breeze.%s' % self.target_storage_engine)
			except ImportError as e:
				self.log.error(str(e))
				raise e
		return self._storage_module

	#
	# COMPUTE (based on engine name)
	#

	# clem 04/05/2016
	@property
	def compute_module(self):
		""" The python module containing an implementation of the compute interface for this target

		this module must include an implementation of compute_interface_module.ComputeInterface,
		and an initiator(ComputeTarget) function

		:rtype: module
		"""
		if not self._compute_module:
			try:
				mod_name = 'breeze.%s_interface' % self.target_engine_name
				self._compute_module = importlib.import_module(mod_name)
			except ImportError as e:
				self.log.error(str(e))
				raise e
		return self._compute_module

	# clem 04/05/2016
	@property
	def compute_interface(self):
		""" The ComputeInterface object to use as the compute interface for this target

		:rtype: breeze.compute_interface_module.ComputeInterface
		"""
		if not self.__compute_interface:
			self.__compute_interface = self.compute_module.initiator(self)
		return self.__compute_interface

	# clem 06/05/2016
	@property
	def runnable(self):
		""" The client Runnable object using this target

		:rtype: Runnable
		"""
		return self._runnable

	# clem 20/06/2016
	@ClassProperty
	def default(cls):
		try:
			return cls.objects.safe_get(pk=settings.DEFAULT_TARGET_ID)
		except ObjectDoesNotExist:
			return ComputeTarget()

	# clem 20/06/2016
	@ClassProperty
	def breeze_default(cls):
		try:
			return cls.objects.safe_get(pk=settings.BREEZE_TARGET_ID)
		except ObjectDoesNotExist:
			return ComputeTarget()

	class Meta(ConfigObject.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_computetarget'


# TODO change from CustomModel to CustomModelAbstract
# TODO change the institute field to a ManyToManyField
class ReportType(FolderObj, CustomModel):
	BASE_FOLDER_NAME = settings.REPORT_TYPE_FN

	# objects = managers.ReportTypeManager()

	type = models.CharField(max_length=17, unique=True)
	description = models.CharField(max_length=5500, blank=True)
	search = models.BooleanField(default=False, help_text="NB : LEAVE THIS UN-CHECKED")
	access = models.ManyToManyField(User, null=True, blank=True, default=None,
		related_name='pipeline_access')  # share list
	targets = models.ManyToManyField(ComputeTarget, null=True, blank=True, default=None,
		related_name='compute_targets')  # available compute targets
	# tags = models.ManyToManyField(Rscripts, blank=True)
	
	# who creates this report
	author = ForeignKey(User)
	# store the institute info of the user who creates this report
	# institute = ForeignKey(Institute, default=Institute.default)
	
	def file_name(self, filename):
		# FIXME check for FolderObj property fitness
		fname, dot, extension = filename.rpartition('.')
		return '%s%s/%s' % (self.BASE_FOLDER_NAME, self.folder_name, filename)
	
	config = models.FileField(upload_to=file_name, blank=True, null=True)
	manual = models.FileField(upload_to=file_name, blank=True, null=True)
	created = models.DateField(auto_now_add=True)

	shiny_report = models.ForeignKey(ShinyReport, help_text="Choose an existing Shiny report to attach it to",
		default=0, blank=True, null=True)

	_all_target_list = None # clem 19/04/2016
	_ready_target_list = None # clem 25/05/2016

	# clem 21/12/2015
	def __init__(self, *args, **kwargs):
		super(ReportType, self).__init__(*args, **kwargs)
		self.__prev_shiny_report = self.shiny_report_id

	@property
	def folder_name(self):
		return '%s_%s' % (self.id, slugify(self.type))

	@property
	def is_shiny_enabled(self):
		""" Is this report associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return self.shiny_report_id > 0 and self.shiny_report.enabled

	# clem 11/12/15
	@property
	def config_path(self):
		""" Return the path of th econfiguration file of this pipeline
		:rtype:
		"""
		return settings.MEDIA_ROOT + str(self.config)

	# clem 11/12/15
	def get_config(self):
		"""
		Return the configuration lines of the pipeline as a string.
		Can be integrated directly into generated script.R
		:rtype: str
		"""
		uri = self.config_path
		conf = ''
		try:
			if isfile(uri):
				conf = str(open(uri).read()) + '\n'
		except IOError:
			pass
		return conf

	def __shiny_changed(self):
		return self.__prev_shiny_report != self.shiny_report_id

	def save(self, *args, **kwargs):

		obj = super(ReportType, self).save(*args, **kwargs) # Call the "real" save() method.
		if not self.read_only:
			if self.__shiny_changed:
				if self.__prev_shiny_report:
					ShinyReport.objects.get(pk=self.__prev_shiny_report).regen_report()
				if self.shiny_report:
					self.shiny_report.regen_report()

			try:
				if not isfile(self.config_path):
					with open(self.config_path, 'w') as f:
						f.write(
							'#	Configuration module (Generated by Breeze)\n#	You can place here any pipeline-wide R config')
			except IOError:
				pass

		return obj

	def __unicode__(self):
		return self.type

	def delete(self, using=None):
		if not self.read_only:
			shiny_r = self.shiny_report
			super(ReportType, self).delete(using=using)
			if shiny_r is not None:
				shiny_r.regen_report()
			return True
		return False

	# clem 26/05/2016
	def _target_objects(cls, only_enabled=False, only_ready=False):
		""" Get possibly available targets for this ReportType

		:param only_enabled: Filter out targets that are not marked as enabled in the DB
		:type only_enabled: bool
		:param only_ready:
			Filter out targets that have disabled dependencies (exec or engine) (this implies only_enabled)
		:type only_ready: bool
		:return:
		:rtype: list[ComputeTarget]
		"""
		targets = cls.targets.filter(enabled=True) if only_enabled or only_ready else cls.targets.all()
		tmp_list = list()
		for each in targets:
			if not only_ready or each.is_operational:
				tmp_list.append(each)
		return tmp_list

	# clem 26/05/2016
	@property
	def enabled_only(self):
		""" A list of enabled ComputeTarget objects that are available to use with this ReportType

		:return:
		:rtype: list[ComputeTarget]
		"""
		return self._target_objects(only_enabled=True)

	# clem 26/05/2016
	@property
	def all(self):
		""" A list of all ComputeTarget objects that are available to use with this ReportType

		:return:
		:rtype: list[ComputeTarget]
		"""
		return self._target_objects()

	# clem 26/05/2016
	@property
	def ready_only(self):
		""" A list of ready to use ComputeTarget objects that are available to use with this ReportType

		This means that they are explicitly marked as enabled in the DB,
		And, each resources they depend on (exec and engine) are also enabled

		:return:
		:rtype: list[ComputeTarget]
		"""
		return self._target_objects(only_ready=True)

	# clem 26/05/2016
	def _gen_targets_form_list(cls, only_ready=False):
		""" Generate a list of tuple from a list of ComputeTarget, This list can be used directly in <select> Form
		obj

		:param only_ready: filter-out non ready targets
		:type only_ready: bool
		:return: (id, label)
		:rtype: list[tuple[int, str]]
		"""
		result_list = list()
		a_list = cls.all if not only_ready else cls.ready_only
		for each in a_list:
			result_list.append(each.as_tuple)
		return result_list

	# clem 19/04/2016
	@property
	def all_as_form_list(self):
		""" A list of tuple, of compute target for this report type, that is suitable to use in a Form

		tuple : (id, label)

		:rtype: list[tuple[int, str]]
		"""
		if not self._all_target_list:
			self._all_target_list = self._gen_targets_form_list()
		return self._all_target_list

	# clem 26/05/2016
	@property
	def ready_as_form_list(self):
		""" A list of tuple, of ready only compute target for this report type, that is suitable to use in a Form

		tuple : (id, label)

		:rtype: list[tuple[int, str]]
		"""
		if not self._ready_target_list:
			self._ready_target_list = self._gen_targets_form_list(only_ready=True)
		return self._ready_target_list

	# clem 19/04/2016
	@property
	def ready_id_list(self):
		""" A list of (enabled & ready) compute target ids for this report type

		:rtype: list[int]
		"""
		result = list()
		for each in self.ready_only:
			result.append(each.id)
		return result

	# TargetManager.targets = targets
	# ez_targets = TargetManager

	# clem 01/06/2016
	def get_all_users_ever(self):
		report_list = Report.objects.filter(_type=self.id).values_list('_author', flat=True).distinct()
		return User.objects.filter(pk__in=report_list)

	# clem 01/06/2016
	def get_all_users_ever_with_count(self):
		report_list = Report.objects.filter(_type=self.id)
		a_dict = dict()
		for each in report_list:
			a_dict[each._author] = 1 + a_dict.get(each._author, 0)
		return a_dict

	class Meta:
		ordering = ('type',)
		abstract = False
		db_table = 'breeze_reporttype'


# from django.db.models.signals import pre_save
# from django.dispatch import receiver

# TODO add a ManyToManyField Institute field
class ScriptCategories(CustomModelAbstract):
	category = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)

	# if the script is a drat then the category should be inactive
	# active = models.BooleanField(default=False)
	
	def __unicode__(self):
		return self.category

	class Meta:
		db_table = 'breeze_script_categories'


class UserDate(models.Model):
	user = ForeignKey(User)
	install_date = models.DateField(auto_now_add=True)
	
	def __unicode__(self):
		return self.user.username

	class Meta:
		db_table = 'breeze_user_date'


# TODO add a ManyToManyField Institute field
class Rscripts(FolderObj, CustomModelAbstract):
	objects = managers.ObjectsWithAuth() # The default manager.

	BASE_FOLDER_NAME = settings.RSCRIPTS_FN

	name = models.CharField(max_length=35, unique=True)
	inln = models.CharField(max_length=150, blank=True)
	details = models.CharField(max_length=5500, blank=True)
	# category = models.CharField(max_length=25, choices=CATEGORY_OPT, default=u'general')
	category = ForeignKey(ScriptCategories, to_field="category")
	author = ForeignKey(User)
	creation_date = models.DateField(auto_now_add=True)
	draft = models.BooleanField(default=True)
	price = models.DecimalField(max_digits=19, decimal_places=2, default=0.00)
	# tag related
	istag = models.BooleanField(default=False)
	must = models.BooleanField(default=False)  # defines wheather the tag is enabled by default
	order = models.DecimalField(max_digits=3, decimal_places=1, blank=True, default=0)
	report_type = models.ManyToManyField(ReportType, null=True, blank=True,
		default=None)  # assosiation with report type
	# report_type = models.ForeignKey(ReportType, null=True, blank=True, default=None)  # assosiation with report type
	access = models.ManyToManyField(User, null=True, blank=True, default=None, related_name="users")
	# install date info
	install_date = models.ManyToManyField(UserDate, blank=True, null=True, default=None, related_name="installdate")
	
	def file_name(self, filename): # TODO check this
		# TODO check for FolderObj fitness
		fname, dot, extension = filename.rpartition('.')
		slug = self.folder_name
		return '%s%s/%s.%s' % (self.BASE_FOLDER_NAME, slug, slug, slugify(extension))
	
	docxml = models.FileField(upload_to=file_name, blank=True)
	code = models.FileField(upload_to=file_name, blank=True)
	header = models.FileField(upload_to=file_name, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	
	def __unicode__(self):
		return self.name

	@property
	def folder_name(self):
		return slugify(self.name)

	@property
	def sec_id(self):
		return 'Section_dbID_%s' % self.id

	@property
	def _code_path(self):
		return settings.MEDIA_ROOT + str(self.code)

	@property
	def _header_path(self):
		return settings.MEDIA_ROOT + str(self.header)

	@property
	def xml_path(self):
		return settings.MEDIA_ROOT + str(self.docxml)

	@property
	def xml_tree(self):
		if not hasattr(self, '_xml_tree'): # caching
			import xml.etree.ElementTree as xml
			self._xml_tree = xml.parse(self.xml_path)
		return self._xml_tree

	def is_valid(self):
		"""
		Return true if the tag XML file is present and non empty
		:return: tell if the tag is usable
		:rtype: bool
		"""
		return is_non_empty_file(self.xml_path)

	# _path_r_template = settings.TAGS_TEMPLATE_PATH
	_path_r_template = settings.SCRIPT_TEMPLATE_PATH

	def get_R_code(self, gen_params, template_file=None):
		"""
		Generates the R code for the report generation of this tag, using the template
		:param gen_params: the result of shell.gen_params_string
		:type gen_params: str
		:return: R code for this tag
		:rtype: str
		"""
		from string import Template

		filein = open(self._path_r_template)
		src = Template(filein.read())
		filein.close()
		# source main code segment
		body = open(self._code_path).read()
		# final step - fire header
		headers = open(self._header_path).read()

		d = {
			'tag_name'  : self.name,
			'body'      : body,
			'gen_params': gen_params,
			'headers'   : headers,
		}
		# do the substitution
		return src.substitute(d)

	# def delete(self, using=None):
	#	super(Rscripts, self).delete(using=using)
	#	return True

	class Meta:
		ordering = ["name"]
		abstract = False
		db_table = 'breeze_rscripts'


# define the table to store the products in user's cart
class CartInfo(CustomModelAbstract):
	script_buyer = ForeignKey(User)
	product = ForeignKey(Rscripts)
	# if free or not
	type_app = models.BooleanField(default=True)
	date_created = models.DateField(auto_now_add=True)
	date_updated = models.DateField(auto_now_add=True)
	# if the user does not pay active == True else active == False
	active = models.BooleanField(default=True)
	
	def __unicode__(self):
		return self.product.name
	
	class Meta:
		ordering = ["active"]


class DataSet(models.Model):
	name = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'datasets/%s.%s' % (slug, extension)
	
	rdata = models.FileField(upload_to=file_name)
	
	def __unicode__(self):
		return self.name


class InputTemplate(models.Model):
	name = models.CharField(max_length=55, unique=True)
	description = models.CharField(max_length=350, blank=True)
	author = ForeignKey(User)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.name)
		return 'mould/%s.%s' % (slug, extension)
	
	file = models.FileField(upload_to=file_name)
	
	def __unicode__(self):
		return self.name


# TODO fix naming of institute
class UserProfile(CustomModelAbstract):
	user = models.ForeignKey(OrderedUser, unique=True)
	
	def file_name(self, filename):
		fname, dot, extension = filename.rpartition('.')
		slug = slugify(self.user.username)
		return 'profiles/%s/%s.%s' % (slug, slug, extension)
	
	fimm_group = models.CharField(max_length=75, blank=True)
	logo = models.FileField(upload_to=file_name, blank=True)
	institute_info = models.ForeignKey(Institute, default=Institute.default)
	# if user accepts the agreement or not
	db_agreement = models.BooleanField(default=False)
	last_active = models.DateTimeField(default=timezone.now)
	
	def __unicode__(self):
		return self.user.get_full_name()  # return self.user.username


class Runnable(FolderObj, CustomModelAbstract):
	##
	# CONSTANTS
	##
	ALLOW_DOWNLOAD = True
	BASE_FOLDER_NAME = ''                            # folder name
	BASE_FOLDER_PATH = ''                            # absolute path to the container folder
	FAILED_FN = settings.FAILED_FN                    # '.failed'
	SUCCESS_FN = settings.SUCCESS_FN                # '.done'
	SUB_DONE_FN = settings.R_DONE_FN                # '.sub_done'
	SH_NAME = settings.GENERAL_SH_NAME                # 'run_job.sh'
	FILE_MAKER_FN = settings.REPORTS_FM_FN            # 'transfer_to_fm.txt'
	INC_RUN_FN = settings.INCOMPLETE_RUN_FN            # '.INCOMPLETE_RUN'
	# output file name (without extension) for nozzle report. MIGHT not be enforced everywhere
	REPORT_FILE_NAME = settings.NOZZLE_REPORT_FN    # 'report'
	RQ_SPECIFICS = ['request_data', 'sections']
	FAILED_TEXT = 'Execution halted'

	HIDDEN_FILES = [SH_NAME, SUCCESS_FN, FILE_MAKER_FN, SUB_DONE_FN] # TODO add FM file ? #
	SYSTEM_FILES = HIDDEN_FILES + [INC_RUN_FN, FAILED_FN]
	# DEFAULT_TARGET = ComputeTarget.objects.get(pk=settings.DEFAULT_TARGET_ID) # TODO DEL

	objects = managers.WorkersManager() # Custom manage

	def __init__(self, *args, **kwargs):
		super(Runnable, self).__init__(*args, **kwargs)
		self.__can_save = False
		self._run_server = None
		# self.R_FILE_NAME = self.r_file_name # backward compatibility only

	##
	# DB FIELDS
	##
	_breeze_stat = models.CharField(max_length=16, default=JobStat.INIT, db_column='breeze_stat')
	_status = models.CharField(max_length=15, blank=True, default=JobStat.INIT, db_column='status')
	progress = models.PositiveSmallIntegerField(default=0)
	sgeid = models.CharField(max_length=15, help_text="job id, as returned by SGE", blank=True)
	# target = ComputeTarget.objects.get(pk=DEFAULT_TARGET.id)

	##
	# WRAPPERS
	##

	__target = None
	__error_msg = ''

	# GENERICS
	def __getattr__(self, item):
		try:
			return super(Runnable, self).__getattribute__(item)
		except AttributeError: # backward compatibility
			return super(Runnable, self).__getattribute__(Trans.swap(item))

	def __setattr__(self, attr_name, value):
		if attr_name == 'breeze_stat':
			self._set_status(value)
		elif attr_name == 'status':
			raise ReadOnlyAttribute # prevent direct writing
		else: # FIXME get rid of that
			attr_name = Trans.swap(attr_name) # backward compatibility

		super(Runnable, self).__setattr__(attr_name, value)

	# clem 06/05/2016
	@property
	def poke_url(self):
		""" Return the url to poke Breeze about this report

		:return: the full url to Breeze
		:rtype: str
		"""
		from django.core.urlresolvers import reverse
		from breeze.views import job_url_hook
		md5 = get_file_md5(self._rexec.path)
		return 'http://%s%s' % (settings.FULL_HOST_NAME, reverse(job_url_hook, args=(self.instance_type[0], self.id, md5)))

	# SPECIFICS

	# clem 08/06/2016
	@property
	def r_file_name(self):
		if self.is_concrete_class: # Only for subclasses :
			return self.target_obj.exec_obj.exec_file_in
		return ''

	# clem 17/09/2015
	@classmethod
	def find_sge_instance(cls, sgeid):
		""" Return a runnable instance from an sge_id

		:param sgeid: an sgeid from qstat
		:type sgeid: str | int
		:rtype: Runnable
		"""
		result = None
		try:
			result = cls.objects.get(sgeid=sgeid)
		except ObjectDoesNotExist:
			pass
		return result

	@property
	def institute(self):
		try:
			self._author.get_profile()
		except ValueError: # for some reason and because of using custom OrderedUser the first call
			# raise this exception while actually populating the cache for this value...
			pass
		return self._author.get_profile().institute_info

	##
	# OTHER SHARED PROPERTIES
	##
	@property # Interface : has to be implemented in Report TODO @abc.abstractmethod ?
	def get_shiny_report(self):
		"""
		To be overridden by Report :
		ShinyReport
		:rtype: ShinyReport | NoneType
		"""
		return None # raise NotImplementedError

	@property # Interface : has to be implemented in Report TODO @abc.abstractmethod ?
	def is_shiny_enabled(self):
		"""
		To be overridden by Report :
		Is this report's type associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return None # raise NotImplementedError

	# Interface : has to be implemented in Report TODO @abc.abstractmethod ?
	def has_access_to_shiny(self, this_user=None):
		"""
		To be overridden by Report
		:type this_user: User | OrderedUser
		:rtype: bool
		"""
		return None # raise NotImplementedError

	@property # UNUSED ?
	def html_path(self):
		return '%s%s' % (self.home_folder_full_path, self.REPORT_FILE_NAME)

	@property # UNUSED ?  # FIXME obsolete
	def _r_out_path(self):
		return self.exec_out_file_path

	@property
	def source_file_path(self):
		if not str(self._rexec).startswith(self.home_folder_full_path): # Quick fix for old style project path
			self._rexec = '%s%s' % (self.home_folder_full_path, os.path.basename(str(self._rexec)))
			self.save()
		return self._rexec.path

	@property # UNUSED ?
	def _html_full_path(self):
		return '%s.html' % self.html_path

	@property
	def _test_file(self):
		"""
		full path of the job competition verification file
		used to store the retval value, that has timings and perf related data

		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.SUCCESS_FN)

	@property  # FIXME obsolete
	def exec_out_file_path(self):
		# return '%s%s' % (self._rexec, self.target_obj.exec_obj.exec_file_out)
		return '%s%s' % (self.home_folder_full_path, self.target_obj.exec_obj.exec_file_out)

	@property
	def failed_file_path(self):
		""" full path of the job failure verification file used to store the retval value, that has timings and perf related data

		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.FAILED_FN)

	@property
	def incomplete_file_path(self):
		"""
		full path of the job incomplete run verification file
		exist only if job was interrupted, or aborted
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.INC_RUN_FN)

	@property  # FIXME obsolete
	def _sge_log_file(self):
		"""
		Return the name of the auto-generated debug/warning file from SGE

		:rtype: str
		"""
		return '%s_%s.o%s' % (self._name.lower(), self.instance_of.__name__, self.sgeid)

	# clem 11/09/2015
	@property
	def _shiny_files(self):
		"""
		Return a list of files related to shiny if applicable, empty list otherwise
		:rtype: list
		"""
		res = list()
		if self.is_report:
			shiny_rep = self.get_shiny_report
			if shiny_rep is not None:
				res = shiny_rep.SYSTEM_FILE_LIST
		return res

	@property
	def _sh_file_path(self):
		"""
		the full path of the sh file used to run the job on the cluster.
		This is the file that SGE has to instruct the cluster to run.
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.SH_NAME)

	# clem 11/09/2015
	@property
	def system_files(self):
		"""
		Return a list of system requires files
		:rtype: list
		"""
		return self.SYSTEM_FILES + [self._sge_log_file] + self._shiny_files

	# clem 16/09/2015
	@property # FIXME obsolete
	def r_error(self):
		""" Returns the last line of script.R which may contain an error message

		:rtype: str
		"""
		out = ''
		if self.is_r_failure:
			lines = open(self.exec_out_file_path).readlines()
			i = len(lines)
			size = i
			for i in range(len(lines) - 1, 0, -1):
				if lines[i].startswith('>'):
					break
			if i != size:
				out = ''.join(lines[i:])[:-1]
		return out

	# clem 11/09/2015
	@property
	def hidden_files(self):
		"""
		Return a list of system required files
		:rtype: list
		"""
		return self.HIDDEN_FILES + [self._sge_log_file, '*~', '*.o%s' % self.sgeid] + self._shiny_files

	# FIXME obsolete
	def _download_ignore(self, cat=None):
		"""
		:type cat: str
		:return: exclude_list, filer_list, name
		:rtype: list, list, str
		"""

		exclude_list = list()
		filer_list = list()
		name = '_full'
		if cat == "-code":
			name = '_Rcode'
			filer_list = ['*.r*', '*.Rout']
		# exclude_list = self.system_files + ['*~']
		elif cat == "-result":
			name = '_result'
			exclude_list = self.hidden_files # + ['*.xml', '*.r*', '*.sh*']
		return exclude_list, filer_list, name

	@property  # FIXME obsolete
	def sge_job_name(self):
		"""The job name to submit to SGE
		:rtype: str
		"""
		name = self._name if not self._name[0].isdigit() else '_%s' % self._name
		return '%s_%s' % (slugify(name), self.instance_type.capitalize())

	@property  # FIXME obsolete
	def is_done(self):
		"""
		Tells if the job run is not running anymore, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		<b>DOES NOT IMPLY ANYTHING ABOUT SUCCESS OF SGE JOB</b>
		INCLUDES : FAILED, ABORTED, SUCCEED
		:rtype: bool
		"""
		# if self._breeze_stat == JobStat.DONE:
		# 	return True
		# return isfile(self._test_file)
		return self._breeze_stat == JobStat.DONE # or isfile(self._test_file)

	@property  # FIXME obsolete
	def is_sge_successful(self):
		"""
		Tells if the job was properly run or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		INCLUDES : ABORTED, SUCCEED
		:rtype: bool
		"""
		return self._status != JobStat.FAILED and self.is_done

	@property  # FIXME obsolete
	def is_successful(self):
		"""
		Tells if the job was successfully done or not, using it's breeze_stat or
		the confirmation file that allow confirmation even in case of management
		system failure (like breeze db being down, breeze server, or the worker)
		This means completed run from sge, no user abort, and verified R success
		:rtype: bool
		"""
		return self._status == JobStat.SUCCEED and self.is_r_successful

	@property  # FIXME obsolete
	def is_r_successful(self):
		"""Tells if the job R job completed successfully
		:rtype: bool
		"""
		return self.is_done and not isfile(self.failed_file_path) and not isfile(self.incomplete_file_path) and \
			   isfile(self.exec_out_file_path)

	@property # FIXME obsolete
	def is_r_failure(self):
		"""Tells if the job R job has failed (not equal to the oposite of is_r_successful)
		:rtype: bool
		"""
		return self.is_done and isfile(self.failed_file_path) and not isfile(self.incomplete_file_path) and \
			   isfile(self.exec_out_file_path)

	@property
	def aborting(self):
		"""Tells if job is being aborted
		:rtype: bool
		"""
		return self.breeze_stat == JobStat.ABORT or self.breeze_stat == JobStat.ABORTED

	##
	# SHARED CONCRETE METHODS (SGE_JOB MANAGEMENT RELATED)
	##
	# FIXME : LEGACY ONLY
	def abort(self):
		""" Abort the job using

		:rtype: bool
		"""
		return self.compute_if.abort()

	def write_sh_file(self):
		""" Generate the SH file that will be executed on the compute target to configure and run the job """
		from os import chmod

		conf_dict = {
			'failed_fn'    : self.FAILED_FN,
			'inc_run_fn'   : self.INC_RUN_FN,
			'success_fn'   : self.SUCCESS_FN,
			'done_fn'      : self.SUB_DONE_FN,
			'in_file_name' : self.target_obj.exec_obj.exec_file_in,
			'out_file_name': self.target_obj.exec_obj.exec_file_out,
			'full_path'    : self.target_obj.exec_obj.exec_bin_path,
			'args'         : self.target_obj.exec_obj.exec_args,
			'cmd'          : self.target_obj.exec_obj.exec_run,
			'failed_txt'   : self.FAILED_TEXT,
			'user'         : self._author,
			'date'         : datetime.now(),
			'tz'           : time.tzname[time.daylight],
			'poke_url'     : self.poke_url,
			'url'          : 'http://%s' % settings.FULL_HOST_NAME,
			'target'       : str(self.target_obj),
			'arch_cmd'     : self.target_obj.exec_obj.exec_arch_cmd,
			'version_cmd'  : self.target_obj.exec_obj.exec_version_cmd,
		}

		gen_file_from_template(settings.BOOTSTRAP_SH_TEMPLATE, conf_dict, self._sh_file_path)

		# config should be readable and executable but not writable, same for script.R
		chmod(self._sh_file_path, ACL.RX_RX_)
		chmod(self.source_file_path, ACL.R_R_)

	# INTERFACE for extending assembling process
	# TODO @abc.abstractmethod ?
	# FIXME obsolete
	def generate_r_file(self, *args, **kwargs):
		""" Place Holder for instance specific R files generation
		THIS METHOD MUST BE overridden in subclasses
		"""
		raise not_imp(self)

	# INTERFACE for extending assembling process
	# TODO @abc.abstractmethod ?
	def deferred_instance_specific(self, *args, **kwargs):
		"""
		Specific operations to generate job or report instance dependencies.
		N.B. : you CANNOT use m2m relations before this point
		THIS METHOD MUST BE overridden in subclasses
		"""
		raise not_imp(self)

	def assemble(self, *args, **kwargs):
		"""
		Assembles instance home folder, configures DRMAA and R related files.
		Call deferred_instance_specific()
		and finally triggers self.save()
		"""
		for each in self.RQ_SPECIFICS:
			if each not in kwargs.keys():
				raise InvalidArguments("'%s' should be provided as an argument of assemble()" % each)

		# The instance is now fully generated and ready to be submitted to SGE
		# NO SAVE can happen before this point, to avoid any inconsistencies
		# that could occur if an Exception happens anywhere in the process
		self.__can_save = True
		self.save()

		if not os.path.exists(self.home_folder_full_path):
			os.makedirs(self.home_folder_full_path, ACL.RWX_RWX_)

		# BUILD instance specific R-File
		self.generate_r_file(*args, **kwargs)
		# other stuff that might be needed by specific kind of instances (Report and Jobs)
		self.deferred_instance_specific(*args, **kwargs)
		# open instance home's folder for other to write
		self.grant_write_access()
		# Build and write SH file
		self.write_sh_file()

		self.save()
		# Triggers target specific code
		self.compute_if.assemble_job()

	def submit_to_cluster(self):
		if not self.aborting:
			from django.utils import timezone
			self.created = timezone.now() # important to be able to timeout sgeid
			self.breeze_stat = JobStat.RUN_WAIT

	# run deleted 21/06/2016

	# FIXME LEGACY ONLY
	@new_thread
	def old_sge_run(self):
		"""
			Submits reports as an R-job to cluster with SGE;
			This submission implements REPORTS concept in BREEZE
			(For SCRIPTS submission see Jobs.run)
		"""
		from os import chdir, system

		s = None
		config = self._sh_file_path

		try:
			chdir(self.home_folder_full_path)
			if self.is_report and self.fm_flag: # Report specific
				system(settings.JDBC_BRIDGE_PATH) # TODO change that

			# *MAY* prevent db from being dropped
			# django.db.close_connection()
			self.breeze_stat = JobStat.PREPARE_RUN
		except Exception as e:
			self.log.exception('pre-run error %s (process continues)' % e)

		try:
			with drmaa_lock:
				with drmaa.Session() as s:
					jt = s.createJobTemplate()
					jt.workingDirectory = self.home_folder_full_path
					jt.jobName = self.sge_job_name
					jt.email = [str(self._author.email)]
					if self.mailing != '':
						jt.nativeSpecification = "-m " + self.mailing
					if self.email is not None and self.email != '':
						jt.email.append(str(self.email))
					jt.blockEmail = False

					jt.remoteCommand = config
					jt.joinFiles = True

					self.progress = 25
					self.save()
					if not self.aborting:
						self.sgeid = copy.deepcopy(s.runJob(jt))
						self.log.debug('returned sge_id "%s"' % self.sgeid)
						self.breeze_stat = JobStat.SUBMITTED
					# waiting for the job to end
					self.waiter(s, True)

					jt.delete()

		except (drmaa.AlreadyActiveSessionException, drmaa.InvalidArgumentException, drmaa.InvalidJobException,
		Exception) as e:
			self.log.error('drmaa submit failed : %s' % e)
			self.manage_run_failed(-1, '')
			# if s is not None:
			#	s.exit()
			raise e

		self.log.debug('drmaa submit ended successfully !')
		return 0

	# FIXME LEGACY INTERFACE ONLY
	def waiter(self, s, drmaa_waiting=False):
		return self.compute_if.busy_waiting(s, drmaa_waiting)

	# FIXME LEGACY ONLY
	@new_thread
	def old_sge_waiter(self, s, drmaa_waiting=False):
		"""

		:param s:
		:type s: drmaa.Session
		:param drmaa_waiting:
		:type drmaa_waiting: bool
		:rtype: drmaa.JobInfo
		"""
		exit_code = 42
		aborted = False
		log = get_logger()
		if self.is_sgeid_empty or self.is_done:
			return
		sge_id = copy.deepcopy(self.sgeid) # useless
		try:
			ret_val = None
			if drmaa_waiting:
				with drmaa_lock:
					with drmaa.Session() as s:
						ret_val = s.wait(sge_id, drmaa.Session.TIMEOUT_WAIT_FOREVER)
			else:
				try:
					while True:
						time.sleep(1)
						self.compute_if.status()
						if self.aborting:
							break
				except NoSuchJob:
					exit_code = 0

			# ?? FIXME
			self.breeze_stat = JobStat.DONE
			self.save()

			# FIXME this is SHITTY
			if self.aborting:
				aborted = True
				exit_code = 1
				self.breeze_stat = JobStat.ABORTED

			if isinstance(ret_val, drmaa.JobInfo):
				if ret_val.hasExited:
					exit_code = ret_val.exitStatus
				# dic = ret_val.resourceUsage # TODO FUTURE use for mail reporting
				aborted = ret_val.wasAborted

			self.progress = 100
			if exit_code == 0:  # normal termination
				self.breeze_stat = JobStat.DONE
				self.log.info('sge job finished !')
				if not self.is_r_successful: # R FAILURE or USER ABORT (to check if that is true)
					self.log.info('exit code %s, SGE success !' % exit_code)
					self.manage_run_failed(ret_val, exit_code, drmaa_waiting, 'r')
				else: # FULL SUCCESS
					self.manage_run_success(ret_val)
			else: # abnormal termination
				if not aborted: # SGE FAILED
					self.log.info('exit code %s, SGE FAILED !' % exit_code)
					self.manage_run_failed(ret_val, exit_code, drmaa_waiting, 'sge')
				else: # USER ABORTED
					self.manage_run_aborted(ret_val, exit_code)
			self.save()
			return exit_code
		except Exception as e:
			self.log.error(' while waiting : %s' % str(e))
			raise e

	@staticmethod  # FIXME obsolete design
	def __auto_json_dump(ret_val, file_n):
		""" Dumps JobInfo ret_val from drmaa to failed or succeed file

		:type ret_val: drmaa.JobInfo
		:type file_n: str
		"""
		import json
		import os

		if isinstance(ret_val, drmaa.JobInfo):
			try:
				os.chmod(file_n, ACL.RW_RW_)
				json.dump(ret_val, open(file_n, 'w+'))
				os.chmod(file_n, ACL.R_R_)
			except Exception as e:
				pass

	# Clem 11/09/2015  # FIXME obsolete design
	def manage_run_success(self, ret_val):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_success'

		Actions on Job successful completion

		:type ret_val: drmaa.JobInfo
		"""
		self.__auto_json_dump(ret_val, self._test_file)
		self.breeze_stat = JobStat.SUCCEED
		self.log.info('SUCCESS !')
		self.trigger_run_success(ret_val)

	# Clem 11/09/2015  # FIXME obsolete design
	def manage_run_aborted(self, ret_val, exit_code):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_user_aborted'

		Actions on Job abortion

		:type ret_val: drmaa.JobInfo
		:type exit_code: int
		"""
		self.breeze_stat = JobStat.ABORTED
		self.log.info('exit code %s, user aborted' % exit_code)
		self.trigger_run_user_aborted(ret_val, exit_code)

	# Clem 11/09/2015  # FIXME obsolete design
	def manage_run_failed(self, ret_val, exit_code, drmaa_waiting=None, failure_type=''):
		""" !!! DO NOT OVERRIDE !!!
		instead do override 'trigger_run_failed'
		Actions on Job Failure

		:type ret_val: int
		:type exit_code: int | str
		:type drmaa_waiting: bool | None
		:type failure_type: str
		"""
		self.__auto_json_dump(ret_val, self.failed_file_path)

		if drmaa_waiting is not None:
			if drmaa_waiting:
				self.log.info('Script has failed while drmaa_waiting ! (%s)' % failure_type)
				self.breeze_stat = JobStat.FAILED
			else:
				self.log.info('Script has failed ! (%s)' % failure_type)
				self.breeze_stat = JobStat.SCRIPT_FAILED

		self.trigger_run_failed(ret_val, exit_code)

	# Clem 11/09/2015
	# TODO @abc.abstractmethod ?
	def trigger_run_success(self, ret_val):
		""" Trigger for subclass to override

		:type ret_val: drmaa.JobInfo
		"""
		pass

	# TODO @abc.abstractmethod ?
	def trigger_run_user_aborted(self, ret_val, exit_code):
		""" Trigger for subclass to override

		:type ret_val: drmaa.JobInfo
		:type exit_code: int
		"""
		pass

	# TODO @abc.abstractmethod ?
	def trigger_run_failed(self, ret_val, exit_code):
		""" Trigger for subclass to override

		:type ret_val: drmaa.JobInfo
		:type exit_code: int
		"""
		pass

	# FIXME obsolete design
	def _set_status(self, status):
		""" Save a specific status state of the instance.
		Changes the progression % and saves the object
		ONLY PLACE WHERE ONE SHOULD CHANGE _breeze_stat and _status
		HAS NOT EFFECT if breeze_stat = DONE

		:param status: a JobStat value
		:type status: str

		"""
		if self._breeze_stat == JobStat.SUCCEED or self._breeze_stat == JobStat.ABORTED or status is None:
			return # Once the job is marked as done, its stat cannot be changed anymore

		# we use JobStat object to provide further extensibility to the job management system
		_status, _breeze_stat, progress, text = JobStat(status).status_logic()
		l1, l2 = '', ''

		if _status is not None:
			l1 = 'status changed from %s to %s' % (self._status, _status) if _status != self._status else ''
			self._status = _status
		if _breeze_stat is not None:
			l2 = 'breeze_stat changed from %s to %s' % (
				self._breeze_stat, _breeze_stat) if _breeze_stat != self._breeze_stat else ''
			self._breeze_stat = _breeze_stat
		if progress is not None:
			self.progress = progress

		total = '%s%s%s' % (l1, ', and ' if l1 != '' and l2 != '' else '', l2)
		if total != '':
			self.log.debug('%s %s%%' % (total, progress))

		self._stat_text = text

		if self.id > 0:
			self.save()

	# FIXME obsolete
	def get_status(self):
		""" Textual representation of current status / NO refresh on _status

		:rtype: str
		"""
		if self.breeze_stat == JobState.SCRIPT_FAILED or (self.breeze_stat == JobState.FAILED and self.is_r_failure):
			return JobState.SCRIPT_FAILED
		if self.breeze_stat == JobState.DONE or self.breeze_stat == JobState.RUNNING:
			return JobStat.textual(self._status, self)
		return JobStat.textual(self.breeze_stat, self)

	@property  # FIXME obsolete
	def is_sgeid_empty(self):
		""" Tells if the job has no sgeid yet

		:rtype: bool
		"""
		return (self.sgeid is None) or self.sgeid == ''

	@property  # FIXME obsolete
	def is_sgeid_timeout(self):
		""" Tells if the waiting time for the job to get an SGEid has expired

		:rtype: bool
		"""
		if self.is_sgeid_empty:
			from datetime import timedelta
			t_delta = timezone.now() - self.created
			self.log.debug('sgeid has been empty for %s sec' % t_delta.seconds)
			assert isinstance(t_delta, timedelta) # code assist only
			return t_delta > timedelta(seconds=settings.NO_SGEID_EXPIRY)
		return False

	# TODO FIXME broken and disabled (WILL FAIL the job)
	def re_submit(self, force=False, duplicate=True):
		""" Reset the job status, so it can be run again
		Use this, if it hadn't had an SGEid or the run was unexpectedly terminated
		DO NOT WORK on SUCCEEDED JOB."""
		self.breeze_stat = JobState.FAILED
		if False: # not self.is_successful or force:
			# TODO finish

			from django.core.files import base
			self.log.info('resetting job status')
			new_name = str(self.name) + '_re'
			old_path = self.home_folder_full_path
			with open(self.source_file_path) as f:
				r_code = f.readlines()

			self.name = new_name

			content = "setwd('%s')\n" % self.home_folder_full_path[:-1] + ''.join(r_code[1:])
			os.rename(old_path, self.home_folder_full_path)
			self.log.debug('renamed to %s' % self.home_folder_full_path)
			self._rexec.save(self.file_name(self.r_file_name), base.ContentFile(content))
			self._doc_ml.name = self.home_folder_full_path + os.path.basename(str(self._doc_ml.name))

			utils.remove_file_safe(self._test_file)
			utils.remove_file_safe(self.failed_file_path)
			utils.remove_file_safe(self.incomplete_file_path)
			utils.remove_file_safe(self._sh_file_path)
			self.save()
			self.write_sh_file()
		# self.submit_to_cluster()

	###
	# DJANGO RELATED FUNCTIONS
	###
	# deleted all_required_are_filled on 13/05/2016 from azure / 7d62c2d for being deprecated

	# TODO check if new item or not
	def save(self, *args, **kwargs):
		if not self.read_only:
			# self.all_required_are_filled()
			if self.id is None and not self.__can_save:
				raise AssertionError('The instance has to complete self.assemble() before any save can happen')
			super(Runnable, self).save(*args, **kwargs) # Call the "real" save() method.
		return False

	def delete(self, using=None):
		if not self.read_only:
			if self._breeze_stat != JobStat.DONE:
				self.abort()
			txt = str(self)
			super(Runnable, self).delete(using=using) # Call the "real" delete() method.
			get_logger().info("%s has been deleted" % txt)
			return True
		return False

	###
	# SPECIAL PROPERTIES FOR INTERFACE INSTANCE
	###

	# clem 13/05/2016
	@property
	def target_obj(self):
		"""

		:return:
		:rtype: ComputeTarget
		"""
		if not self.__target and self.is_concrete_class: # only concrete classes
			# instance level caching
			key = '%s:%s' % (self.instance_type, self.short_id)
			# module level caching
			cached = ObjectCache.get(key)
			if not cached:
				# instance level caching
				if self.is_report and self.target:
					assert isinstance(self.target, ComputeTarget)
					self.__target = self.target
				else:
					self.__target = ComputeTarget.default  # self.DEFAULT_TARGET
				# module level caching
				ObjectCache.add(self.__target, key)
			else:
				self.__target = cached
			self.__target._runnable = self
		return self.__target

	# clem 17/05/2016
	@property
	def compute_module(self):
		return self.target_obj.compute_module

	# clem 06/05/2016
	@property
	def compute_if(self):
		return self.target_obj.compute_interface

	@property
	def is_report(self):
		return isinstance(self, Report)

	@property
	def is_job(self):
		return isinstance(self, Jobs)

	# clem 08/06/2016
	@property
	def is_concrete_class(self):
		""" Tells if this instance is an implementation of Runnable or not (i.e. a subclass)

		:rtype: bool
		"""
		# While Runnable is not a subclass of its subclasses, it's a subclass of itself,
		# thus the negation over the inverted order
		return not issubclass(Runnable, self.__class__)

	@property
	def instance_type(self):
		return self.instance_of.__name__.lower()

	@property
	def instance_of(self):
		# return Report if self.is_report else Jobs if self.is_job else self.__class__
		return self.__class__

	@property
	def md5(self):
		"""
		Return the md5 of the current object status
		Used for long_poll refresh
		:return:
		:rtype: str
		"""
		from hashlib import md5
		m = md5()
		m.update(u'%s%s%s' % (self.text_id, self.get_status(), self.sgeid))
		return m.hexdigest()

	@property
	def short_id_tuple(self):
		""" one letter : r or j followed by the instance id from db
		i.e. r3569 j7823 ...

		:return: a short version of this instance id
		:rtype: (str, int)
		"""
		return self.instance_type[0], self.id

	# clem 11/05/2016
	@property
	def short_id(self):
		return '%s%s' % self.short_id_tuple

	@property
	def text_id(self):
		return '%s %s' % (self.short_id, self.name)

	# clem 11/05/2016
	@property
	def log(self):
		return self.log_custom(1)

	# clem 11/05/2016
	def log_custom(self, level=0):
		log_obj = LoggerAdapter(get_logger(level=level + 1), dict())
		log_obj.process = lambda msg, kwargs: ('%s : %s' % (self.short_id, msg), kwargs)
		return log_obj

	def __unicode__(self): # Python 3: def __str__(self):
		return u'%s' % self.text_id

	class Meta:
		abstract = True


class Jobs(Runnable):
	# DEFAULT_TARGET = ComputeTarget.objects.get(pk=settings.BREEZE_TARGET_ID)
	DEFAULT_TARGET = ComputeTarget.breeze_default

	def __init__(self, *args, **kwargs):

		super(Jobs, self).__init__(*args, **kwargs)
		allowed_keys = Trans.translation.keys()

		self.__dict__.update((k, v) for k, v in kwargs.iteritems() if k in allowed_keys)

	##
	# CONSTANTS
	##
	BASE_FOLDER_NAME = settings.JOBS_FN
	BASE_FOLDER_PATH = settings.JOBS_PATH
	SH_FILE = settings.JOBS_SH
	# RQ_SPECIFICS = ['request_data', 'sections']
	##
	# DB FIELDS
	##
	_name = models.CharField(max_length=55, db_column='jname')
	_description = models.CharField(max_length=4900, blank=True, db_column='jdetails')
	_author = ForeignKey(User, db_column='juser_id')
	_type = ForeignKey(Rscripts, db_column='script_id')
	_created = models.DateTimeField(auto_now_add=True, db_column='staged')
	target = None # ComputeTarget.objects.get(pk=2)

	def _institute(self):
		return self.institute

	def file_name(self, filename):
		return super(Jobs, self).file_name(filename)

	_rexec = models.FileField(upload_to=file_name, db_column='rexecut')
	_doc_ml = models.FileField(upload_to=file_name, db_column='docxml')

	# Jobs specific
	mailing = models.CharField(max_length=3, blank=True, help_text= \
		'configuration of mailing events : (b)egin (e)nd  (a)bort or empty')  # TextField(name="mailing", )
	email = models.CharField(max_length=75,
		help_text="mail address to send the notification to (not working ATM : your personal mail adress will be user instead)")

	@property
	def folder_name(self):
		return slugify('%s_%s' % (self._name, self._author))

	_path_r_template = settings.SCRIPT_TEMPLATE_PATH

	@property
	def xml_tree(self):
		if not hasattr(self, '_xml_tree'): # caching
			import xml.etree.ElementTree as xml
			self._xml_tree = xml.parse(self._doc_ml.path)
		return self._xml_tree

	def deferred_instance_specific(self, *args, **kwargs):
		if 'sections' in kwargs:
			tree = kwargs.pop('sections')
			a_path = self.file_name('form.xml')
			tree.write(a_path)
			self._doc_ml = a_path
		else:
			raise InvalidArgument
		# kwargs['sections'].write(str(settings.TEMP_FOLDER) + 'job.xml') # change with ml

	# TODO merge inside of runnable
	def generate_r_file(self, *args, **kwargs):
		"""
		generate the Nozzle generator R file
		:param tree: Rscripts tree from xml
		:type tree: ?
		:param request_data:
		:type request_data: HttpRequest
		"""
		from django.core.files import base
		# from breeze import shell as rshell

		# params = rshell.gen_params_string_job_temp(sections, request_data.POST, self, request_data.FILES) # TODO funct
		params = self.gen_params_string_job_temp(*args, **kwargs)
		code = "setwd('%s')\n%s\n" % (self.home_folder_full_path[:-1], self._type.get_R_code(params))
		code += 'system("touch %s")' % self.SUB_DONE_FN

		# save r-file
		self._rexec.save(self.r_file_name, base.ContentFile(code))

	# def gen_params_string_job_temp(tree, data, runnable_inst, files, custom_form):
	# TODO merge with the report
	def gen_params_string_job_temp(self, *args, **kwargs):
		"""
			Iterates over script's/tag's parameters to bind param names and user input;
			Produces a (R-specific) string with one parameter definition per lines,
			so the string can be pushed directly to R file.
		"""
		import re
		# can be replaced by
		# return gen_params_string(tree, data, runnable_inst, files)

		tree = kwargs.pop('sections', None)
		request_data = kwargs.pop('request_data', None)
		data = kwargs.pop('custom_form', None)
		files = request_data.FILES

		tmp = dict()
		params = ''
		# FIXME no access to cleaned data here
		for item in tree.getroot().iter('inputItem'): # for item in tree.getroot().iter('inputItem'):
			#  item.set('val', str(data.cleaned_data[item.attrib['comment']]))
			if item.attrib['type'] == 'CHB':
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(
					data.cleaned_data[item.attrib['comment']]).upper() + '\n'
			elif item.attrib['type'] == 'NUM':
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(
					data.cleaned_data[item.attrib['comment']]) + '\n'
			elif item.attrib['type'] == 'TAR':
				lst = re.split(', |,|\n|\r| ', str(data.cleaned_data[item.attrib['comment']]))
				seq = 'c('
				for itm in lst:
					if itm != "":
						seq += '\"%s\",' % itm

				seq = seq + ')' if lst == [''] else seq[:-1] + ')'
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
			elif item.attrib['type'] == 'FIL' or item.attrib['type'] == 'TPL':
				# add_file_to_job(jname, juser, FILES[item.attrib['comment']])
				# add_file_to_report(runnable_inst.home_folder_full_path, files[item.attrib['comment']])
				self.add_file(files[item.attrib['comment']])
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(
					data.cleaned_data[item.attrib['comment']]) + '"\n'
			elif item.attrib['type'] == 'DTS':
				path_to_datasets = str(settings.MEDIA_ROOT) + "datasets/"
				slug = slugify(data.cleaned_data[item.attrib['comment']]) + '.RData'
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(path_to_datasets) + str(slug) + '"\n'
			elif item.attrib['type'] == 'MLT':
				res = ''
				seq = 'c('
				for itm in data.cleaned_data[item.attrib['comment']]:
					if itm != "":
						res += str(itm) + ','
						seq += '\"%s\",' % itm
				seq = seq[:-1] + ')'
				item.set('val', res[:-1])
				params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
			else:  # for text, text_are, drop_down, radio
				params = params + str(item.attrib['rvarname']) + ' <- "' + str(
					data.cleaned_data[item.attrib['comment']]) + '"\n'
		return params

	class Meta(Runnable.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_jobs'


class Report(Runnable):
	def __init__(self, *args, **kwargs):
		super(Report, self).__init__(*args, **kwargs)
		allowed_keys = Trans.translation.keys() + ['shared', 'title', 'project', 'rora_id']
		self.__dict__.update((k, v) for k, v in kwargs.iteritems() if k in allowed_keys)

	##
	# CONSTANTS
	##
	BASE_FOLDER_NAME = settings.REPORTS_FN
	BASE_FOLDER_PATH = settings.REPORTS_PATH
	SH_FILE = settings.REPORTS_SH
	# RQ_SPECIFICS = ['request_data', 'sections']
	##
	# DB FIELDS
	##
	_name = models.CharField(max_length=55, db_column='name')
	_description = models.CharField(max_length=350, blank=True, db_column='description')
	_author = ForeignKey(User, db_column='author_id')
	_type = models.ForeignKey(ReportType, db_column='type_id')
	_created = models.DateTimeField(auto_now_add=True, db_column='created')
	_institute = ForeignKey(Institute, default=Institute.default, db_column='institute_id')

	# TODO change to StatusModel cf https://django-model-utils.readthedocs.org/en/latest/models.html#statusmodel

	def file_name(self, filename):
		return super(Report, self).file_name(filename)

	_rexec = models.FileField(upload_to=file_name, blank=True, db_column='rexec')
	_doc_ml = models.FileField(upload_to=file_name, blank=True, db_column='dochtml')
	email = ''
	mailing = ''

	# Report specific
	project = models.ForeignKey(Project, null=True, blank=True, default=None)
	shared = models.ManyToManyField(User, null=True, blank=True, default=None, related_name='report_shares')
	conf_params = models.TextField(null=True, editable=False)
	conf_files = models.TextField(null=True, editable=False)
	fm_flag = models.BooleanField(default=False)
	target = models.ForeignKey(ComputeTarget, default=ComputeTarget.default)
	# Shiny specific
	shiny_key = models.CharField(max_length=64, null=True, editable=False)
	rora_id = models.PositiveIntegerField(default=0)

	##
	# Defining meta props
	##
	# 25/06/15
	@property
	def folder_name(self):
		return slugify('%s_%s_%s' % (self.id, self._name, self._author.username))

	# 26/06/15
	@property
	def _dochtml(self):
		return '%s%s' % (self.home_folder_full_path, settings.NOZZLE_REPORT_FN)

	# @property
	# def _rtype_config_path(self):
	#	return settings.MEDIA_ROOT + str(self._type.config)

	@property
	def title(self):
		return u'%s Report :: %s  <br>  %s' % (self.type, unicode(self.name).decode('utf8'), self.type.description)

	@property
	def fm_file_path(self):
		"""
		The full path of the file use for FileMaker transfer
		:rtype: str
		"""
		return '%s%s' % (self.home_folder_full_path, self.FILE_MAKER_FN)

	@property
	def nozzle_url(self):
		"""
		Return the url to nozzle view of this report
		:return: the url to nozzle view of this report
		:rtype: str
		"""
		from django.core.urlresolvers import reverse
		from breeze import views

		return reverse(views.report_file_view, kwargs={ 'rid': self.id })



	# 04/06/2015
	@property # TODO check
	def args_string(self):
		""" The query string to be passed for shiny apps, if Report is Shiny-enabled, or blank string	"""
		from django.utils.http import urlencode

		if self.rora_id > 0:
			return '?%s' % urlencode([('path', self.home_folder_rel), ('roraId', str(self.rora_id))])
		else:
			return ''

	# clem 02/10/2015
	@property
	def get_shiny_report(self):
		"""
		:rtype: ShinyReport
		"""
		if self.is_shiny_enabled:
			return self._type.shiny_report
		return ShinyReport()

	# clem 05/10/2015
	@property
	def shiny_url(self):
		"""
		:rtype: str
		"""
		return self.get_shiny_report.url(self)

	# clem 11/09/2015
	@property
	def is_shiny_enabled(self):
		""" Is this report's type associated to a ShinyReport, and if so is this ShinyReport enabled ?
		:rtype: bool
		"""
		return self._type.is_shiny_enabled

	def has_access_to_shiny(self, this_user=None):
		"""
		States if specific user is entitled to access this report through Shiny and if this report is entitled to Shiny
		And the attached Shiny Report if any is Enabled
		:type this_user: User | OrderedUser
		:rtype: bool
		"""
		assert isinstance(this_user, (User, OrderedUser))
		return this_user and (this_user in self.shared.all() or self._author == this_user) \
			   and self.is_shiny_enabled

	# clem 23/09/2015
	@property
	def remote_shiny_path(self):
		if self.shiny_key is None or self.shiny_key == '':
			if self.is_shiny_enabled:
				self.generate_shiny_key()
				self.save()
		# return settings.SHINY_REMOTE_BREEZE_REPORTS_PATH + self.shiny_key
		return '%s%s/' % (settings.SHINY_REMOTE_BREEZE_REPORTS_PATH, self.shiny_key)

	_path_r_template = settings.NOZZLE_REPORT_TEMPLATE_PATH

	def deferred_instance_specific(self, *args, **kwargs):
		import pickle
		import json

		request_data = kwargs['request_data']# self.request_data
		# sections = kwargs['sections']

		# clem : saves parameters into db, in order to be able to duplicate report
		self.conf_params = pickle.dumps(request_data.POST)
		if request_data.FILES:
			tmp = dict()
			for each in request_data.FILES:
				tmp[str(each)] = str(request_data.FILES[each])
			self.conf_files = json.dumps(tmp)
		# self.save()

		# generate shiny access for offsite users
		if self.is_shiny_enabled:
			self.generate_shiny_key()

		if 'shared_users' in kwargs.keys():
			self.shared = kwargs['shared_users']

	_path_tag_r_template = settings.TAGS_TEMPLATE_PATH

	# TODO : use clean or save ?
	# def generate_r_file(self, sections, request_data):
	def generate_r_file(self, *args, **kwargs):
		"""
		generate the Nozzle generator R file

		:param sections: Rscripts list
		:param request_data: HttpRequest
		"""
		from string import Template
		from django.core.files import base
		from breeze import shell as rshell
		import xml.etree.ElementTree as XmlET

		sections = kwargs.pop('sections', list())
		request_data = kwargs.pop('request_data', None)
		# custom_form = kwargs.pop('custom_form', None)

		report_specific = open(self._path_tag_r_template).read()

		filein = open(self._path_r_template)
		src = Template(filein.read())
		filein.close()
		tag_list = list()
		self.fm_flag = False
		for tag in sections:
			assert (isinstance(tag, Rscripts)) # useful for code assistance ONLY
			if tag.is_valid() and tag.sec_id in request_data.POST and request_data.POST[tag.sec_id] == '1':
				tree = XmlET.parse(tag.xml_path)
				if tag.name == "Import to FileMaker":
					self.fm_flag = True

				# TODO : Find a way to solve this dependency issue
				gen_params = rshell.gen_params_string(tree, request_data.POST, self,
					request_data.FILES)
				# tag_list.append(tag.get_R_code(gen_params) + report_specific)
				tag_list.append(tag.get_R_code(gen_params) + Template(report_specific).substitute(
					{ 'loc': self.home_folder_full_path[:-1] }))

		d = {
			'loc'               : self.home_folder_full_path[:-1],
			'report_name'       : self.title,
			'project_parameters': self.dump_project_parameters,
			'pipeline_config'   : self.dump_pipeline_config,
			'tags'              : '\n'.join(tag_list),
			'dochtml'           : str(self._dochtml),
			'sub_done'          : self.SUB_DONE_FN,
		}
		# do the substitution
		result = src.substitute(d)
		# save r-file
		self._rexec.save(self.target_obj.exec_obj.exec_file_in, base.ContentFile(result))

	# Clem 11/09/2015
	def trigger_run_success(self, ret_val):
		"""
		Specific actions to do on SUCCESSFUL report runs
		:type ret_val: drmaa.JobInfo
		"""
		import os
		# TODO even migrate to SGE
		if self.is_report and self.fm_flag and isfile(self.fm_file_path):
			run = open(self.fm_file_path).read().split("\"")[1]
			os.system(run)

	@property
	def dump_project_parameters(self):
		import copy

		dump = '# <----------  Project Details  ----------> \n'
		dump += 'report.author          <- \"%s\"\n' % self.author.username
		dump += 'report.pipeline        <- \"%s\"\n' % self.type
		dump += 'project.name           <- \"%s\"\n' % self.project.name
		dump += 'project.manager        <- \"%s\"\n' % self.project.manager
		dump += 'project.pi             <- \"%s\"\n' % self.project.pi
		dump += 'project.author         <- \"%s\"\n' % self.project.author
		dump += 'project.collaborative  <- \"%s\"\n' % self.project.collaborative
		dump += 'project.wbs            <- \"%s\"\n' % self.project.wbs
		dump += 'project.external.id    <- \"%s\"\n' % self.project.external_id
		dump += '# <----------  end of Project Details  ----------> \n\n'

		return copy.copy(dump)

	@property
	def dump_pipeline_config(self):
		import copy

		dump = '# <----------  Pipeline Config  ----------> \n'
		dump += 'query.key          <- \"%s\"  # id of queried RORA instance \n' % self.rora_id
		dump += self._type.get_config() # 11/12/15
		dump += '# <------- end of Pipeline Config --------> \n\n\n'

		return copy.copy(dump)

	def generate_shiny_key(self):
		"""
		Generate a sha256 key for outside access
		"""
		from datetime import datetime
		from hashlib import sha256

		m = sha256()
		m.update(settings.SECRET_KEY + self.folder_name + str(datetime.now()))
		self.shiny_key = str(m.hexdigest())

	def save(self, *args, **kwargs):
		super(Report, self).save(*args, **kwargs) # Call the "real" save() method.
		# if self.type.shiny_report_id > 0 and len(self._home_folder_rel) > 1:
		if self.is_shiny_enabled and self.is_successful:
			# call symbolic link update
			self.type.shiny_report.link_report(self, True, self.get_shiny_report.make_remote_too)

	def delete(self, using=None):
		if self.type.shiny_report_id > 0:
			self.type.shiny_report.unlink_report(self)

		return super(Report, self).delete(using=using) # Call the "real" delete() method.

	class Meta(Runnable.Meta): # TODO check if inheritance is required here
		abstract = False
		db_table = 'breeze_report'


class ShinyTag(CustomModel):
	# ACL_RW_RW_R = 0664
	FILE_UI_NAME = settings.SHINY_UI_FILE_NAME
	FILE_SERVER_NAME = settings.SHINY_SERVER_FILE_NAME
	# FILE_DASH_UI = settings.SHINY_DASH_UI_FILE
	TAG_FOLDER = settings.SHINY_TAGS
	RES_FOLDER = settings.SHINY_RES_FOLDER
	FILE_TEMPLATE = settings.SHINY_TAG_CANVAS_PATH
	FILE_TEMPLATE_URL = settings.MOULD_URL + settings.SHINY_TAG_CANVAS_FN
	DEFAULT_MENU_ITEM = 'menuItem("Quality Control", icon = icon("filter", lib = "glyphicon"), tabName = "REPLACE BY THE NAME OF YOUR TAG IN UPPER CASE HERE",' \
						'badgeLabel = "QC", badgeColor = "green")'

	name = models.CharField(max_length=55, unique=True, blank=False,
		help_text="Must be unique, no special characters, no withe spaces."
				  "<br />NB : Use the same (in upper case) in the tabName field of the menu entry")
	# label = models.CharField(max_length=32, blank=False, help_text="The text to be display on the dashboard")
	description = models.CharField(max_length=350, blank=True, help_text="Optional description text")
	author = ForeignKey(OrderedUser)
	created = models.DateTimeField(auto_now_add=True)
	# institute = ForeignKey(Institute, default=Institute.default)
	order = models.PositiveIntegerField(default=0, help_text="sorting index number (0 is the topmost)")
	menu_entry = models.TextField(default=DEFAULT_MENU_ITEM,
		help_text="Use menuItem or other Shiny  Dashboard items to customize the menu entry "
				  "of your tag.<br /><u>NB : tabName MUST be identical to the uppercase name of your tag.</u>")

	@property
	def get_name(self):
		return str(slugify(str(self.name)))

	@staticmethod
	def remove_file_safe(fname):
		import os.path
		from django.db.models.fields.files import FieldFile
		if type(fname) == file or type(fname) == FieldFile:
			fname = fname.path
		try:
			if os.path.isfile(fname):
				os.remove(fname)
		except os.error:
			pass

	def folder_name_gen(self, remote=False):
		return str('%s%s/' % (self.TAG_FOLDER if not remote else settings.SHINY_REMOTE_TAGS, self.get_name))

	@property
	def folder_name_remote_internal(self):
		return str('%s%s/' % (settings.SHINY_REMOTE_TAGS_INTERNAL, self.get_name))

	@property
	def folder_name(self):
		return self.folder_name_gen()

	def path_dashboard_server(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.FILE_SERVER_NAME))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.FILE_SERVER_NAME))

	def path_dashboard_body(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.FILE_UI_NAME))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.FILE_UI_NAME))

	def path_res_folder_gen(self, remote=False):
		if not remote:
			return str('%s%s' % (self.folder_name, self.RES_FOLDER))
		else:
			return str('%s%s' % (self.folder_name_remote_internal, self.RES_FOLDER))

	@property
	def path_res_folder(self):
		return self.path_res_folder_gen()

	def file_name_zip(self, filename):
		import os
		base = os.path.splitext(os.path.basename(filename))
		path = str('%s%s_%s.%s' % (settings.UPLOAD_FOLDER, self.get_name, slugify(base[0]), slugify(base[1])))
		return str(path)

	zip_file = models.FileField(upload_to=file_name_zip, blank=True, null=False,
		help_text="Upload a zip file containing all the files required for your tag, and "
				  " following the structure of the <a href='%s'>provided canvas</a>.<br />\n"
				  "Check the <a href='%s'>available libraries</a>. If the one you need is not"
				  " present, please contact an admin." %
				  (FILE_TEMPLATE_URL, settings.SHINY_LIBS_TARGET_URL))
	enabled = models.BooleanField()
	attached_report = models.ManyToManyField(ShinyReport)

	# clem 22/12/2015
	def __init__(self, *args, **kwargs):
		super(ShinyTag, self).__init__(*args, **kwargs)
		self.__prev_reports = list()
		if self.id:
			self.__prev_reports = list(self.attached_report.all() or None)
		self.__prev_name = self.name or None

	# clem 05/10/2015
	def copy_to_remote(self):
		import os
		log_obj = get_logger()
		log_obj.debug("updating %s on RemoteShiny" % self.__repr__)

		# del the remote report copy folder
		path = self.folder_name_gen(True)
		if not os.path.isdir(path) or safe_rm(path):
			try:
				# copy the data content of the report
				safe_copytree(self.folder_name, path)
			except Exception as e:
				log_obj.warning("%s copy error %s" % (self.__repr__, e))
			return True
		log_obj.warning("failed to copy %s to %s" % (self.__repr__, path))
		return False

	def save(self, *args, **kwargs):
		import shutil
		import os
		import zipfile

		# zf = kwargs.pop('zf', None)
		zf = None
		try:
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			pass
		# rebuild = kwargs.pop('rebuild', False)

		new_name = self.name
		if self.name != self.__prev_name and self.__prev_name:
			# name has changed we should rename the folder as well
			self.name = self.__prev_name
			logger.debug(str(('old path :', self.folder_name[:-1], 'to:', new_name)))
			old_dir = self.folder_name[:-1]
			self.name = new_name
			shutil.move(old_dir, self.folder_name[:-1])

		if zf:
			# clear the folder
			shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
			logger.debug(str(('new path:', self.folder_name[:-1])))

			# extract the zip
			zf.extractall(path=self.folder_name)
			# changing files permission
			for item in os.listdir(self.folder_name[:-1]):
				path = '%s%s' % (self.folder_name, item)
				if os.path.isfile(path):
					os.chmod(path, ACL.RW_RW_)
			# removes the zip from temp upload folder
			self._zip_clean()

		super(ShinyTag, self).save(*args, **kwargs) # Call the "real" save() method.

		# refresh ??
		# self = ShinyTag.objects.get(pk=self.id)

		if self.enabled and ShinyReport.remote_shiny_ready():
			self.copy_to_remote()
		logger.debug(str(('before list', self.__prev_reports)))
		logger.debug(str(('after list', self.attached_report.all())))
		for each in (CustomList(self.attached_report.all()).union(self.__prev_reports)).unique():
			each.regen_report()

	# clem 22/12/2015
	def _zip_clean(self): # removes the zip from temp upload folder (thus forcing re-upload)
		import os
		if os.path.isfile(self.zip_file.path):
			self.remove_file_safe(self.zip_file.path)

	# Manages folder creation, zip verification and extraction
	def clean(self):
		import zipfile
		if self.__prev_reports and len(self.__prev_reports):
			logger.debug(str(('list before', self.__prev_reports)))  # self.attached_report.all()
		log_obj = get_logger()

		# checks if attached list changed :
		# shared_users = request_data.POST.getlist('shared')
		##
		# Zip file and folder management
		##
		try: # loads zip file
			zf = zipfile.ZipFile(self.zip_file)
		except Exception as e:
			zf = None
			self._zip_clean()
			if self.id: # not the first time this item is saved, so no problem
				log_obj.info("%s, No zip submitted, no rebuilding" % self.__repr__)
				# rebuild = False
				return # self.save()
			else:
				raise ValidationError({ 'zip_file': ["while loading zip_lib says : %s" % e] })
		# check both ui.R and server.R are in the zip and non empty
		for filename in [self.FILE_SERVER_NAME, self.FILE_UI_NAME]:
			try:
				info = zf.getinfo(filename)
			except KeyError:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["%s not found in zip's root" % filename] })
			except Exception as e:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["while listing zip_lib says : %s" % e] })
			# check that the file is not empty
			if info.file_size < settings.SHINY_MIN_FILE_SIZE:
				self._zip_clean()
				raise ValidationError({ 'zip_file': ["%s file is empty" % filename] })
		log_obj.info("%s, Rebuilding..." % self.__repr__)

	def delete(self, using=None):
		import shutil

		log_obj = get_logger()
		log_obj.info("deleted %s" % self.__repr__)

		# Deleting the folder
		shutil.rmtree(self.folder_name[:-1], ignore_errors=True)
		super(ShinyTag, self).delete(using=using) # Call the "real" delete() method.

	class Meta:
		ordering = ('order',)

	def __repr__(self):
		return '<%s %s:%s>' % (self.__class__.__name__, self.id, self.__unicode__())

	def __unicode__(self):
		return self.name


class OffsiteUser(CustomModel):
	first_name = models.CharField(max_length=32, blank=False, help_text="First name of the off-site user to add")
	last_name = models.CharField(max_length=32, blank=False, help_text="Last name of the off-site user to add")
	email = models.CharField(max_length=64, blank=False, unique=True,
		help_text="Valid email address of the off-site user")
	# institute = models.CharField(max_length=32, blank=True, help_text="Institute name of the off-site user")
	role = models.CharField(max_length=32, blank=True, help_text="Position/role of this off-site user")
	user_key = models.CharField(max_length=32, null=False, blank=False, unique=True, help_text="!! DO NOT EDIT !!")
	added_by = ForeignKey(User, related_name='owner', help_text="!! DO NOT EDIT !!")
	belongs_to = models.ManyToManyField(User, related_name='display', help_text="!! DO NOT EDIT !!")

	created = models.DateTimeField(auto_now_add=True)
	shiny_access = models.ManyToManyField(Report, blank=True)

	@property
	def firstname(self):
		return unicode(self.first_name).capitalize()

	@property
	def lastname(self):
		return unicode(self.last_name).capitalize()

	@property
	def full_name(self):
		return self.firstname + ' ' + self.lastname

	@property
	def fullname(self):
		return self.full_name

	class Meta:
		ordering = ('first_name',)

	# 04/06/2015
	def unlink(self, user):
		"""
		Remove the reference of user to this off-site user
		This off-site user, won't show up in user contact list any more
			and won't have access to any previously shared by this user
		:param user: current logged in user, usually : request.user
		:type user: User
		"""
		# removes access to any report user might have shared with him
		rep_list = self.shiny_access.filter(author=user)
		for each in rep_list:
			self.shiny_access.remove(each)
		# remove the attachment link
		self.belongs_to.remove(user)

	def delete(self, using=None, force=None, *args, **kwargs):
		"""
		Remove this off-site user from the database, provided no user reference it anymore
		:param force: force deletion and remove any remaining reference (shiny_access and belongs_to)
		:type force: bool
		:return: if actually deleted from database
		:rtype: bool
		"""
		if force: # delete any relation to this off-site user
			self.belongs_to.clear()
			self.shiny_access.clear()
		# if no other breeze user reference this off-site user, we remove it
		att_list = self.belongs_to.all()
		if att_list.count() == 0:
			super(OffsiteUser, self).delete(*args, **kwargs)
		else:
			return False
		return True

	def drop(self, user):
		"""
		Remove this off-site user from the user contact list, and remove any access it has to report shared by user
		If any other user reference this  off-site user, it won't be deleted.
		You can force this contact to be totally removed by using .delete(force=True)
		:param user: current logged in user, usually : request.user
		:type user: User
		"""
		self.unlink(user)
		self.delete()

	def __unicode__(self):
		return unicode(self.full_name)
