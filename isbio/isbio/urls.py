"""isbio URL Configuration

The `urlpatterns` list routes URLs to breeze.views., name='breeze.views.' For more information please see:
	https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
	1. Add an import:  from my_app import views
	2. Add a URL to urlpatterns:  url(r'^$', breeze.views.home, name='home')
Class-based views
	1. Add an import:  from other_app.views import Home
	2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
	1. Import the include() function: from django.conf.urls import url, include
	2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.conf import settings
from django.contrib.staticfiles.views import serve
from breeze.middlewares import is_on

if not is_on():
	from down import views

	urlpatterns = [url(r'^.*$', breeze.views.down, name='breeze.views.down')]
else:
	from django.contrib.staticfiles.urls import staticfiles_urlpatterns
	import breeze
	# Uncomment/comment the next two lines to enable/disable the admin:
	from django.contrib import admin
	admin.autodiscover()

	email_pattern = r'\b[\w.\'-]+@(?:(?:[^_+,!@#$%^&*();\/\\|<>"\'\n -][-\w]+[^_+,!@#$%^&*();\/\\|<>"\' ' \
		r'\n-]|\w+)\.)+\w{2,63}\b'

	urlpatterns = [
		url(r'^', include('hello_auth.urls')),
		url(r'^auth/', include('django_auth0.urls')),
		url(r'^user_list/?$', breeze.views.user_list, name='breeze.views.user_list'),
		url(r'^test1/?', breeze.views.job_list, name='breeze.views.job_list'),
		url(r'^mail_list/?$', breeze.views.user_list_advanced, name='breeze.views.user_list_advanced'),
		url(r'^custom_list/?$', breeze.views.custom_list, name='breeze.views.custom_list'),
		# url(r'^$', django_cas_login),  # breeze.views.breeze, name='breeze.views.breeze'),
		url(r'^breeze/?$', breeze.views.breeze, name='breeze.views.breeze'),
		# url(r'^logout/?$', django_cas_logout),  # breeze.views.logout, name='breeze.views.logout'),
		url(r'^stat/?$', breeze.views.ajax_user_stat, name='breeze.views.ajax_user_stat'),
		# Special system checks
		# url(r'^resources/restart/?$', breeze.views.restart_breeze, name='breeze.views.restart_breeze'),
		# url(r'^resources/restart-vm/?$', breeze.views.restart_vm, name='breeze.views.restart_vm'),
		url(r'^status/fs_info/?$', breeze.views.file_system_info, name='breeze.views.file_system_info'),
		url(r'^status/fs_info/fix_file/(?P<fid>\d+)$', breeze.views.fix_file_acl, name='breeze.views.fix_file_acl'),
		url(r'^status/log/?$', breeze.views.view_log, name='breeze.views.view_log'),
		url(r'^status/log/all/?$', breeze.views.view_log, { 'show_all': True }, name='breeze.views.view_log'),
		url(r'^status/log/(?P<num>\d+)/?$', breeze.views.view_log, name='breeze.views.view_log'),
		url(r'^status/fs_ok/?$', breeze.views.check_file_system_coherent, name='breeze.views.check_file_system_coherent'),
		url(r'^status/qstat/?$', breeze.views.qstat_live, name='breeze.views.qstat_live'),
		url(r'^status_lp/qstat/(?P<md5_t>[a-z0-9_]{32})?$', breeze.views.qstat_lp, name='breeze.views.qstat_lp'),
		# All others system check in a wrapper
		url(r'^status/(?P<what>[a-z_-]+)?/?$', breeze.views.checker, name='breeze.views.checker'),
		url(r'^home/(?P<state>[a-z]+)?$', breeze.views.home, name='home'),
		url(r'^ajax-rora-patients/(?P<which>[a-z]+)?$', breeze.views.ajax_patients_data, name='breeze.views.ajax_patients_data'),
		url(r'^ajax-rora/action/?$', breeze.views.ajax_rora_action, name='breeze.views.ajax_rora_action'),
		url(r'^ajax-rora-plain-screens/(?P<gid>\d+)$', breeze.views.ajax_rora_screens, name='breeze.views.ajax_rora_screens'),
		url(r'^ajax-rora-groupname/?$', breeze.views.group_name, name='breeze.views.group_name'),
		url(r'^update-user-info/?$', breeze.views.update_user_info_dialog, name='update_user_info_dialog'),
		url(r'^update-server/?$', breeze.views.update_server, name='breeze.views.update_server'),
		url(r'^help/?$', breeze.views.dochelp, name='breeze.views.dochelp'),
		# url(r'^db-policy/?$', breeze.views.db_policy, name='breeze.views.db_policy'),
		url(r'^store/?$', breeze.views.store, name='store'),
		url(r'^store/deletefree/?$', breeze.views.deletefree, name='breeze.views.deletefree'),
		url(r'^installscripts/(?P<sid>\d+)$', breeze.views.install, name='breeze.views.install'),
		url(r'^installreport/(?P<sid>\d+)$', breeze.views.installreport, name='breeze.views.installreport'),
		url(r'^mycart/?$', breeze.views.my_cart, name='breeze.views.my_cart'),
		url(r'^updatecart/?$', breeze.views.update_cart, name='breeze.views.update_cart'),
		url(r'^addtocart/(?P<sid>\d+)$', breeze.views.add_to_cart, name='breeze.views.add_to_cart'),
		url(r'^abortreports/(?P<rid>\d+)$', breeze.views.abort_report, name='breeze.views.abort_report'),
		url(r'^abortjobs/(?P<jid>\d+)$', breeze.views.abort_job, name='breeze.views.abort_job'),
		url(r'^search/(?P<what>[a-z]+)?$', breeze.views.search, name='breeze.views.search'),
		url(r'^patient-data/(?P<which>\d+)?$', breeze.views.ajax_patients, name='breeze.views.ajax_patients'),
		url(r'^patient-new/?$', breeze.views.ajax_patients_new, name='breeze.views.ajax_patients_new'),
		url(r'^screen-data/(?P<which>\d+)?$', breeze.views.screen_data, name='breeze.views.screen_data'),
		url(r'^showdetails/(?P<sid>\d+)$', breeze.views.showdetails, name='breeze.views.showdetails'),
		url(r'^deletecart/(?P<sid>\d+)$', breeze.views.deletecart, name='breeze.views.deletecart'),
		url(r'^reports/?$', breeze.views.reports, name='breeze.views.reports'),
		url(r'^reports/search$', breeze.views.report_search, name='breeze.views.report_search'),
		url(r'^reports/view/(?P<rid>\d+)/(?P<fname>.+)?$', breeze.views.report_file_view, name='report.view'),
		url(r'^reports/get/(?P<rid>\d+)/(?P<fname>.+)?$', breeze.views.report_file_get, name='breeze.views.report_file_get'),
		url(r'^media/reports/(?P<rid>\d+)_(?P<rest>[^/]+)/(?P<fname>.+)?$', breeze.views.report_file_wrap, name='breeze.views.report_file_wrap'),
		url(r'^media/reports/(?P<rid>\d+)/(?P<fname>.+)?$', breeze.views.report_file_wrap2, name='breeze.views.report_file_wrap2'),
		url(r'^reports/delete/(?P<rid>\d+)(?P<redir>-[a-z]+)?$', breeze.views.delete_report, name='breeze.views.delete_report'),
		url(r'^reports/edit_access/(?P<rid>\d+)$', breeze.views.edit_report_access, name='breeze.views.edit_report_access'),
		url(r'^reports/overview/(?P<rtype>\w+)-(?P<iname>[^/-]+)-(?P<iid>[^/-]+)$', breeze.views.report_overview, name='breeze.views.report_overview'),
		url(r'^reports/edit/(?P<jid>\d+)?$', breeze.views.edit_report, name='breeze.views.edit_report'),  # Re Run report
		url(r'^reports/check/?$', breeze.views.check_reports, name='breeze.views.check_reports'),  # Re Run report
		url(r'^reports/send/(?P<rid>\d+)$', breeze.views.send_report, name='breeze.views.send_report'),
		url(r'^off_user/add/?$', breeze.views.add_offsite_user_dialog, name='breeze.views.add_offsite_user_dialog'),
		url(r'^off_user/add/(?P<rid>\d*)$', breeze.views.add_offsite_user_dialog, name='breeze.views.add_offsite_user_dialog'),
		url(r'^off_user/add/form/(?P<email>' + email_pattern + ')$', breeze.views.add_offsite_user, name='breeze.views.add_offsite_user'),
		url(r'^off_user/add/form/?$', breeze.views.add_offsite_user, name='breeze.views.add_offsite_user'),
		url(r'^off_user/edit/(?P<uid>\d*)$', breeze.views.edit_offsite_user, name='breeze.views.edit_offsite_user'),
		url(r'^off_user/del/(?P<uid>\d*)$', breeze.views.delete_off_site_user, name='breeze.views.delete_off_site_user'),
		# Shiny page in
		# url(r'^reports/shiny-tab/(?P<rid>\d+)/?$', breeze.views.report_shiny_view_tab, name='breeze.views.report_shiny_view_tab'),
		url(r'^runnable/delete/?', breeze.views.runnable_del, name='breeze.views.runnable_del'),
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?$', breeze.views.jobs, name='jobs'),
		url(r'^jobs/delete/(?P<jid>\d+)(?P<state>[a-z]+)?$', breeze.views.delete_job, name='breeze.views.delete_job'), # FIXME DEPRECATED
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?delete/(?P<jid>\d+)$', breeze.views.delete_job, name='breeze.views.delete_job'),
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?group-delete/?$', breeze.views.runnable_del, name='breeze.views.runnable_del'),
		url(r'^jobs/run/(?P<jid>\d+)$', breeze.views.run_script, name='breeze.views.run_script'), # FIXME DEPRECATED
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?run/(?P<jid>\d+)$', breeze.views.run_script, name='breeze.views.run_script'),
		url(r'^jobs/edit/jobs/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.edit_job, name='breeze.views.edit_job'), # FIXME DEPRECATED
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?edit/jobs/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.edit_job, name='breeze.views.edit_job'),
		url(r'^jobs/edit/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.edit_job, name='breeze.views.edit_job'), # FIXME DEPRECATED
		url(r'^jobs/(?P<page>\d+)?(/)?(?P<state>[a-z]+)?(/)?edit/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.edit_job, name='breeze.views.edit_job'),
		url(r'^jobs/show-code/(?P<jid>\d+)$', breeze.views.show_rcode, name='breeze.views.show_rcode'),
		url(r'^jobs/download/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.send_zipfile_j, name='breeze.views.send_zipfile_j'),
		url(r'^report/download/(?P<jid>\d+)(?P<mod>-[a-z]+)?$', breeze.views.send_zipfile_r, name='breeze.views.send_zipfile_r'),
		# url(r'^update-jobs/(?P<jid>\d+)-(?P<item>[a-z]+)$', breeze.views.update_jobs, name='breeze.views.update_jobs'), # FIXME DEPRECATED
		url(r'^jobs/info/(?P<jid>\d+)-(?P<item>[a-z]+)$', breeze.views.update_jobs, name='breeze.views.update_jobs'), # FIXME DEPRECATED
		url(r'^jobs/info/(?P<item>[a-z]+)/(?P<jid>\d+)$', breeze.views.update_jobs, name='breeze.views.update_jobs'),
		url(r'^jobs/info/(?P<jid>\d+)$', breeze.views.update_jobs, { 'item': 'script' }, name='breeze.views.update_jobs'),
		url(r'^reports/info/(?P<jid>\d+)$', breeze.views.update_jobs, { 'item': 'report' }, name='breeze.views.update_jobs'),
		# new
		url(r'^jobs/info_lp/(?P<jid>\d+)/(?P<md5_t>[a-z0-9_]{32})?$', breeze.views.update_jobs_lp, { 'item': 'script' }, name='breeze.views.update_jobs_lp'),
		url(r'^reports/info_lp/(?P<jid>\d+)/(?P<md5_t>[a-z0-9_]{32})?$', breeze.views.update_jobs_lp, { 'item': 'report' }, name='breeze.views.update_jobs_lp'),
		url(r'^hook/(?P<i_type>r|j)(?P<rid>\d+)/(?P<md5>[a-z0-9_]{32})/(?P<status>\w+)?$', breeze.views.job_url_hook, name='breeze.views.job_url_hook'),
		url(r'^hook/(?P<i_type>r|j)(?P<rid>\d+)/(?P<md5>[a-z0-9_]{32})/(?P<status>\w+)/(?P<code>\w+)?$', breeze.views.job_url_hook, name='breeze.views.job_url_hook'),
		# url(r'^update-all-jobs/$', breeze.views.update_all_jobs, name='breeze.views.update_all_jobs'), # DO NOT USE : TOOOOOOOO SLOW
		url(r'^scripts/new/?$', breeze.views.new_script_dialog, name='scripts.new'),
		url(r'^scripts/delete/(?P<sid>\d+)$', breeze.views.delete_script, name='breeze.views.delete_script'),
		url(r'^scripts/apply-script/(?P<sid>\d+)$', breeze.views.create_job, name='scripts.apply'),
		url(r'^scripts/read-descr/(?P<sid>\d+)$', breeze.views.read_descr, name='scripts.read_desc'),
		url(r'^scripts/(?P<layout>[a-z]+)?$', breeze.views.scripts, name='breeze.views.scripts'),
		url(r'^new/append/(?P<which>[A-Z]+)$', breeze.views.append_param, name='breeze.views.append_param'),
		url(r'^new/delete/(?P<which>.+)$', breeze.views.delete_param, name='breeze.views.delete_param'),
		url(r'^new/?$', breeze.views.create_script, name='breeze.views.create_script'),
		url(r'^pipelines/new/?$', breeze.views.new_rtype_dialog, name='breeze.views.new_rtype_dialog'), # TODO
		url(r'^new-rtype/?$', breeze.views.new_rtype_dialog, name='breeze.views.new_rtype_dialog'),
		url(r'^projects/create/?$', breeze.views.new_project_dialog, name='breeze.views.new_project_dialog'),
		url(r'^projects/edit/(?P<pid>\d+)$', breeze.views.edit_project_dialog, name='breeze.views.edit_project_dialog'),
		url(r'^projects/view/(?P<pid>\d+)$', breeze.views.veiw_project, name='breeze.views.veiw_project'),
		url(r'^projects/delete/(?P<pid>\d+)$', breeze.views.delete_project, name='breeze.views.delete_project'),
		url(r'^groups/create/?$', breeze.views.new_group_dialog, name='breeze.views.new_group_dialog'),
		url(r'^groups/edit/(?P<gid>\d+)$', breeze.views.edit_group_dialog, name='breeze.views.edit_group_dialog'),
		url(r'^groups/view/(?P<gid>\d+)$', breeze.views.view_group, name='breeze.views.view_group'),
		url(r'^groups/delete/(?P<gid>\d+)$', breeze.views.delete_group, name='breeze.views.delete_group'),
		url(r'^submit/?$', breeze.views.save, name='breeze.views.save'),
		url(r'^get/template/(?P<name>[^/]+)$', breeze.views.send_template, name='get.template'),
		url(r'^get/(?P<ftype>[a-z]+)-(?P<fname>[^/-]+)$', breeze.views.send_file, name='breeze.views.send_file'),
		url(r'^builder/?$', breeze.views.builder, name='breeze.views.builder'),
		url(r'^invalidate/??$', breeze.views.invalidate_cache, name='breeze.views.invalidate_cache'),
		url(r'^resources/?$', breeze.views.resources, name='res'),
		url(r'^resources/invalidate_cache/?$', breeze.views.invalidate_cache_view, name='cache.invalidate'),
		url(r'^resources/scripts/(?P<page>\d+)?$', breeze.views.manage_scripts, name='res.scripts'),
		url(r'^resources/scripts/all/(?P<page>\d+)?$', breeze.views.manage_scripts, { 'view_all': True }, name='res.scripts.all'),
		url(r'^resources/scripts/(all/)?script-editor/(?P<sid>\d+)(?P<tab>-[a-z_]+)?$', breeze.views.script_editor, name='breeze.views.script_editor'),
		url(r'^resources/scripts/(all/)?script-editor/update/(?P<sid>\d+)$', breeze.views.script_editor_update, name='breeze.views.script_editor_update'),
		url(r'^resources/scripts/(all/)?script-editor/get-content/(?P<content>[^/-]+)(?P<iid>-\d+)?$', breeze.views.send_dbcontent, name='breeze.views.send_dbcontent'),
		url(r'^resources/scripts/(all/)?script-editor/get-code/(?P<sid>\d+)/(?P<sfile>[^/-]+)$', breeze.views.get_rcode, name='breeze.views.get_rcode'),
		url(r'^resources/scripts/(all/)?script-editor/get-form/(?P<sid>\d+)$', breeze.views.get_form, name='breeze.views.get_form'),
		url(r'^resources/pipes/?$', breeze.views.manage_pipes, name='breeze.views.manage_pipes'),
		url(r'^resources/pipes/pipe-editor/(?P<pid>\d+)$', breeze.views.edit_rtype_dialog, name='breeze.views.edit_rtype_dialog'),
		url(r'^resources/pipes/delete/(?P<pid>\d+)$', breeze.views.delete_pipe, name='breeze.views.delete_pipe'),
		url(r'^resources/datasets/?$', breeze.views.manage_scripts, name='breeze.views.manage_scripts'),
		url(r'^resources/files/?$', breeze.views.manage_scripts, name='breeze.views.manage_scripts'),
		url(r'^resources/integration/?$', breeze.views.manage_scripts, name='breeze.views.manage_scripts'),
		url(r'^media/scripts/(?P<path>[^.]*(\.(jpg|jpeg|gif|png)))?$', serve,
			{'document_root': settings.MEDIA_ROOT + 'scripts/'}),
		url(r'^media/pipelines/(?P<path>[^.]*(\.(pdf)))$', serve,
			{'document_root': settings.MEDIA_ROOT + 'pipelines/'}),
		url(r'^media/mould/(?P<path>.*)$', serve,
			{'document_root': settings.MEDIA_ROOT + 'mould/'}),

		# url(r'^media/(?P<path>.*)$', 'django.breeze.views.static.serve', name='breeze.views.static.serve'',
		# 			{'document_root': settings.MEDIA_ROOT}),
		# Examples:
		# url(r'^$', 'isbio.breeze.views.home', name='home'),
		# url(r'^isbio/', include('isbio.foo.urls')),

		# Uncomment the admin/doc line below to enable admin documentation:
		# url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

		# Uncomment/comment the next line to enable/disable the admin:
		url(r'^admin/?', include(admin.site.urls)),
	]

	if settings.DEBUG and settings.DEV_MODE:

		urlpatterns += [
			url(r'^closed$', serve, { 'path': '', }),
			# url(r'^static/(?P<path>.*)$', serve)
		]
	# print staticfiles_urlpatterns()
	urlpatterns += staticfiles_urlpatterns()
