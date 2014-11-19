import os, shutil, re, stat, copy
from datetime import datetime
from multiprocessing import Process
import xml.etree.ElementTree as xml
from Bio import Entrez
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.files import File, base
import breeze.models
import auxiliary as aux
import logging

import socket
if socket.gethostname().startswith('breeze'):
    import drmaa

logger = logging.getLogger(__name__)

def init_script(name, inline, person):
    spath = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts" , name, None))

    if not os.path.isdir(spath):
        os.makedirs(spath)
        dbitem = breeze.models.Rscripts(name=name, category=breeze.models.Script_categories.objects.get(category="general"), inln=inline, author=person, details="empty", order=0)

        # create empty files for header, code and xml
        dbitem.header.save('name.txt', base.ContentFile('# write your header here...'))
        dbitem.code.save('name.r', base.ContentFile('# copy and paste main code here...'))
        dbitem.save()

        root = xml.Element('rScript')
        root.attrib['ID'] = str(dbitem.id)
        input_array = xml.Element('inputArray')
        input_array.text = "empty"
        root.append(input_array)

        newxml = open(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person), 'w')
        xml.ElementTree(root).write(newxml)
        newxml.close()

        dbitem.docxml.save('script.xml', File(open(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person))))
        dbitem.save()
        os.remove(str(settings.TEMP_FOLDER) + 'script_%s.xml' % (person))
        # dbitem.docxml.save('name.xml', base.ContentFile(''))

        return spath

    return False

def init_pipeline(form):
    """
        Initiates a new RetortType item in the DB.
        Creates a folder for initial pipeline data.
    """
    # First Save the data that comes with a form:
    # 'type', 'description', 'search', 'access'
    new_pipeline = form.save()

    # Add configuration file
    new_pipeline.config.save('config.txt', base.ContentFile('#          Configuration Module  \n'))
    new_pipeline.save()

    return True

def update_script_dasics(script, form):
    """
        Update script name and its inline description. In case of a new name it
        careates a new folder for script and makes file copies but preserves db istance id
    """

    if str(script.name) != str(form.cleaned_data['name']):
        new_folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts", str(form.cleaned_data['name']), None))
        old_folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts", script.name, None))
        new_slug = slugify(form.cleaned_data['name'])

        if not os.path.isdir(new_folder):
            os.makedirs(new_folder)
            script.name = form.cleaned_data['name']
            script.inln = form.cleaned_data['inline']
            script.save()
            # copy folder
            files_list = os.listdir(old_folder)
            for item in files_list:
                fileName, fileExtension = os.path.splitext(item)
                # shutil.copy2(old_folder + item, str(new_folder) + str(new_slug) + str(fileExtension))
                if fileExtension == '.xml':
                    script.docxml.save('name.xml', File(open(old_folder + item)))
                elif fileExtension == '.txt':
                    script.header.save('name.txt', File(open(old_folder + item)))
                elif fileExtension == '.r' or fileExtension == '.R':
                    script.code.save('name.r', File(open(old_folder + item)))
                else:
                    script.logo.save('name' + str(fileExtension), File(open(old_folder + item)))

            # delete old folder
            shutil.rmtree(old_folder)

            script.creation_date = datetime.now()
            script.save()
        return True
    else:
        script.inln = form.cleaned_data['inline']
        script.creation_date = datetime.now()
        script.save()
        return True

def update_script_description(script, post_data):
    script.details = str(post_data['description_field'])
    script.creation_date = datetime.now()
    script.save()
    return True

def update_script_xml(script, xml_data):
    file_path = str(settings.MEDIA_ROOT) + str(script.docxml)

    if os.path.isfile(file_path):
        handle = open(file_path, 'w')
        handle.write(str(xml_data))
        handle.close()

        script.creation_date = datetime.now()
        script.save()
        return True
    else:
        return False

def update_script_sources(script, post_data):
    if post_data['source_file'] == 'Header':
        file_path = settings.MEDIA_ROOT + str(script.header)
    elif post_data['source_file'] == 'Main':
        file_path = settings.MEDIA_ROOT + str(script.code)

    handle = open(file_path, 'w')
    handle.write(str(post_data['mirrorEditor']))
    handle.close()

    script.creation_date = datetime.now()
    script.save()
    return True

def update_script_logo(script, pic):
    if script.logo:
        os.remove(str(settings.MEDIA_ROOT) + str(script.logo))

    script.logo = pic
    script.creation_date = datetime.now()
    script.save()
    return True

def del_script(script):
    folder = str(settings.MEDIA_ROOT) + str(get_folder_name("scripts" , script.name, None))

    if os.path.isdir(folder):
        shutil.rmtree(folder)
        script.delete()
        return True

    return False

def del_pipe(pipe):
    slug = slugify(str(pipe.id) + '_' + pipe.type)
    folder = str(settings.MEDIA_ROOT) + 'pipelines/%s/' % (slug)

    if os.path.isdir(folder):
        shutil.rmtree(folder)
        pipe.delete()
        return True

    return False

def del_report(report):
    path = str(settings.MEDIA_ROOT) + report.home

    if os.path.isdir(path):
        shutil.rmtree(path)
    report.delete()

    return True

def del_job(job):
    docxml_path = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))

    if os.path.isdir(docxml_path):
        shutil.rmtree(docxml_path)
    job.delete()
    return True

def schedule_job(job, mailing):
    """
        Creates SGE configuration file for QSUB command
    """
    job_path = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    config_path = job_path + slugify(job.jname + '_' + job.juser.username) + '_config.sh'
    config = open(config_path, 'w')

    st = os.stat(config_path)  # config should be executble
    os.chmod(config_path, st.st_mode | stat.S_IEXEC)

    command = '#!/bin/bash \n' + str(settings.R_ENGINE_PATH) + 'CMD BATCH --no-save ' + str(settings.MEDIA_ROOT) + str(job.rexecut)
    config.write(command)
    config.close()

    job.progress = 0
    job.save()
    return 1


def run_job(job, script=None):
    """
        Submits scripts as an R-job to cluster with qsub (SGE);
        This submission implements SCRIPTS concept in BREEZE
        (For REPOTS submission see run_report)
    """
    loc = str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', job.jname, job.juser.username))
    config = loc + slugify(job.jname + '_' + job.juser.username) + '_config.sh'

    default_dir = os.getcwd()
    os.chdir(loc)

    job.status = "active"
    job.progress = 15
    job.save()

    s = drmaa.Session()
    s.initialize()

    jt = s.createJobTemplate()

    jt.workingDirectory = loc
    jt.jobName = slugify(job.jname) + '_JOB'
    jt.email = [str(job.juser.email)]
    jt.blockEmail = False
    jt.remoteCommand = config
    jt.joinFiles = True

    job.sgeid = s.runJob(jt)
    job.progress = 30
    job.save()

    SGEID = copy.deepcopy(job.sgeid)
    # waiting for the job to end
    #if not SGEID:
	#print "no id!"
    retval = s.wait(SGEID, drmaa.Session.TIMEOUT_WAIT_FOREVER)
    job.progress = 100
    job.save()

    if retval.hasExited and retval.exitStatus == 0:
        job.status = 'succeed'

        # clean up the folder

    else:
        job.status = 'failed'

    job.save()
    s.exit()
    os.chdir(default_dir)
    return True

def run_report(report, fmFlag):
    """
        Submits reports as an R-job to cluster with SGE;
        This submission implements REPORTS concept in BREEZE
        (For SCRIPTS submission see run_job)
    """
    
    
    loc = str(settings.MEDIA_ROOT) + report.home
    config = loc + '/sgeconfig.sh'
    default_dir = os.getcwd()
    os.chdir(loc)
    

    if fmFlag:
        os.system("/projects/fhrb_pm/bin/start-jdbc-bridge")

    report.status = "active"
    report.progress = 15
    report.save()
   
    

    s = drmaa.Session()
    s.initialize()

    jt = s.createJobTemplate()

    jt.workingDirectory = loc
    jt.jobName = slugify(report.name) + '_REPORT'
    jt.email = [str(report.author.email)]
    jt.blockEmail = False
    jt.remoteCommand = config
    jt.joinFiles = True
    
    #print()

    report.sgeid = s.runJob(jt)
    report.progress = 30
    report.save()

    # waiting for the job to end
    SGEID = copy.deepcopy(report.sgeid)
    print(SGEID)
    retval = s.wait(SGEID, drmaa.Session.TIMEOUT_WAIT_FOREVER)
    report.progress = 100
    report.save()

    if retval.hasExited and retval.exitStatus == 0:
        report.status = 'succeed'

        # clean up the folder

    else:
        report.status = 'failed'

    report.save()
    
    # aux.open_folder_permissions(loc, 0777)

    os.chdir(default_dir)

    if fmFlag:
        extra_path = loc + "/transfer_to_fm.txt"
        extra_file = open(extra_path, 'r')
        command = extra_file.read()
        run = command.split("\"")[1]
        os.system(run)
    s.exit()
    return True

def abort_report(report):
    
    s = drmaa.Session()
    s.initialize()
    #print("hello!")
    s.control(report.sgeid, drmaa.JobControlAction.TERMINATE)
    report.status = "aborted"
    report.save()
    s.exit()
    
    return True

def track_sge_job(job):
    status = str(job.status)
    #    decodestatus = {
    #        drmaa.JobState.UNDETERMINED: 'process status cannot be determined',
    #        drmaa.JobState.QUEUED_ACTIVE: 'job is queued and active',
    #        drmaa.JobState.SYSTEM_ON_HOLD: 'job is queued and in system hold',
    #        drmaa.JobState.USER_ON_HOLD: 'job is queued and in user hold',
    #        drmaa.JobState.USER_SYSTEM_ON_HOLD: 'job is queued and in user and system hold',
    #        drmaa.JobState.RUNNING: 'job is running',
    #        drmaa.JobState.SYSTEM_SUSPENDED: 'job is system suspended',
    #        drmaa.JobState.USER_SUSPENDED: 'job is user suspended',
    #        drmaa.JobState.DONE: 'job finished normally',
    #        drmaa.JobState.FAILED: 'job finished, but failed',
    #        }

    # s = drmaa.Session()
    # s.initialize()

    # status = str(s.jobStatus(job.id))
    # s.exit()

    if status == 'queued_active':
        job.progress = 35
    elif status == 'running':
        job.progress = 55
    elif status == 'done' or status == 'failed':
        job.progress = 100

    job.save()

    return status

def assemble_job_folder(jname, juser, tree, data, code, header, FILES):
    """
        Builds (singe) R-exacutable file: puts together sources, header
        and input parameters from user
    """

    # create job folder
    directory = get_job_folder(jname, juser)
    if not os.path.exists(directory):
        os.makedirs(directory)

    rexec = open(str(settings.TEMP_FOLDER) + 'rexec.r', 'w')
    script_header = open(str(settings.MEDIA_ROOT) + str(header), "rb").read()
    script_code = open(str(settings.MEDIA_ROOT) + str(code), "rb").read()

    params = ''
    for item in tree.getroot().iter('inputItem'):
        item.set('val', str(data.cleaned_data[item.attrib['comment']]))
        if item.attrib['type'] == 'CHB':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]).upper() + '\n'
        elif item.attrib['type'] == 'NUM':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.cleaned_data[item.attrib['comment']]) + '\n'
        elif item.attrib['type'] == 'TAR':
            lst = re.split(', |,|\n|\r| ', str(data.cleaned_data[item.attrib['comment']]))
            seq = 'c('
            for itm in lst:
                if itm != "":
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        elif item.attrib['type'] == 'FIL' or item.attrib['type'] == 'TPL':
            add_file_to_job(jname, juser, FILES[item.attrib['comment']])
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'
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
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            item.set('val', res[:-1])
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        else:  # for text, text_are, drop_down, radio
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.cleaned_data[item.attrib['comment']]) + '"\n'

    tree.write(str(settings.TEMP_FOLDER) + 'job.xml')

    rexec.write("setwd(\"%s\")\n" % directory)
    rexec.write("#####################################\n")
    rexec.write("###       Code Section            ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_code)
    rexec.write("\n\n#####################################\n")
    rexec.write("### Parameters Definition Section ###\n")
    rexec.write("#####################################\n")
    rexec.write(params)
    rexec.write("\n\n#####################################\n")
    rexec.write("###       Assembly Section        ###\n")
    rexec.write("#####################################\n")
    rexec.write(script_header)

    rexec.close()
    return 1

def build_header(data):
    header = open(str(settings.TEMP_FOLDER) + 'header.txt', 'w')
    string = str(data)
    header.write(string)
    header.close()
    return header

def add_file_to_report(directory, f):
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + "/" + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def add_file_to_job(job_name, user_name, f):
    directory = get_job_folder(job_name, user_name)

    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(directory + f.name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def get_job_folder(name, user=None):
    return str(settings.MEDIA_ROOT) + str(get_folder_name('jobs', name, user))

def get_folder_name(loc, name, user=None):
    if loc == "jobs":
        slug = slugify(name + '_' + str(user))
    else:
        slug = slugify(name)
    return '%s/%s/' % (loc, slug)

def get_dataset_info(path):
    path = str(settings.MEDIA_ROOT) + str(path)
    lst = list()

#    r('library(vcd)')
#    r.assign('dataset', str(path))
#    r('load(dataset)')
#    r('dataSet1 <- sangerSet[1:131,]')
#    drugs = r('featureNames(dataSet1)')
#
#    for pill in drugs:
#        lst.append(dict(name=str(pill), db="Sanger.RData"))

    return lst

def gen_params_string(docxml, data, dir, files):
    """
        Iterates over script's/tag's parameters to bind param names and user input;
        Produces a (R-specific) string with one parameter definition per lines,
        so the string can be pushed directly to R file.
    """
    params = str()
    for item in docxml.getroot().iter('inputItem'):
        if item.attrib['type'] == 'CHB':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.get(item.attrib['comment'], "NA")).upper() + '\n'
        elif item.attrib['type'] == 'NUM':
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(data.get(item.attrib['comment'], "NA")) + '\n'
        elif item.attrib['type'] == 'TAR':
            lst = re.split(', |,|\n|\r| ', str(data.get(item.attrib['comment'], "NA")))
            seq = 'c('
            for itm in lst:
                if itm != "":
                    seq = seq + '\"%s\",' % itm

            if lst == ['']:
                seq = seq + ')'
            else:
                seq = seq[:-1] + ')'
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        elif item.attrib['type'] == 'FIL' or item.attrib['type'] == 'TPL':

            if files:
                try:
                    add_file_to_report(dir, files[item.attrib['comment']])
                    params = params + str(item.attrib['rvarname']) + ' <- "' + str(files[item.attrib['comment']].name) + '"\n'
                except:
                    pass
            else:
                params = params + str(item.attrib['rvarname']) + ' <- ""\n'
        elif item.attrib['type'] == 'DTS':
            path_to_datasets = str(settings.MEDIA_ROOT) + "datasets/"
            slug = slugify(data.get(item.attrib['comment'], "NA")) + '.RData'
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(path_to_datasets) + str(slug) + '"\n'
        elif item.attrib['type'] == 'MLT':
            res = ''
            seq = 'c('
            for itm in data.getlist(item.attrib['comment'], "NA"):
                if itm != "":
                    res += str(itm) + ','
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            item.set('val', res[:-1])
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        elif item.attrib['type'] == 'DTM_SAMPLES':
            res = ''
            seq = 'c('
            for itm in data.getlist(item.attrib['comment'], "NA"):
                if itm != "":
                    res += str(itm) + ','
                    seq = seq + '\"%s\",' % itm
            seq = seq[:-1] + ')'
            item.set('val', res[:-1])
            params = params + '# First character of each element in the vector below\n# serves to distinguish Group (G) and Sample (S) Ids;\n# ! You have to trim each element to get original Id !\n'
            params = params + str(item.attrib['rvarname']) + ' <- ' + str(seq) + '\n'
        else:  # for text, text_are, drop_down, radio
            params = params + str(item.attrib['rvarname']) + ' <- "' + str(data.get(item.attrib['comment'], "NA")) + '"\n'

    return params

def report_search(data_set, report_type, query):
    """
        Each report type assumes its own search implementation;
        RPy2 could be a good option (use local installation on VM):
            - each report is assosiated with an r-script for searching;
            - each report should have another r-script to generate an overview
    """
    lst = list()

    # !!! HANDLE EXCEPTIONS IN THIS FUNCTION !!! #

    # GENE - Entrez search with BioPython #
    if str(report_type) == 'Gene' and len(query) > 0:
        Entrez.email = "dmitrii.bychkov@helsinki.fi"  # <- bring user's email here
        instance = str(query) + '[Gene/Protein Name]'  #  e.g. 'DMPK[Gene/Protein Name]'
        species = 'Homo sapiens[Organism]'
        search_query = instance + ' AND ' + species
        handle = Entrez.esearch(db='gene', term=search_query)
        record = Entrez.read(handle)

        for item in record['IdList']:
            record_summary = Entrez.esummary(db='gene', id=item)
            record_summary = Entrez.read(record_summary)
            if record_summary[0]['Name']:
                lst.append(dict(id=str(record_summary[0]['Id']), name=str(record_summary[0]['Name']), db='Entrez[Gene]'))

    # Other report types should be implemented in a generalized way! #
    else:
        pass

    return lst

def get_report_overview(report_type, instance_name, instance_id):
    """
        Most likely will call rCode to generate overview in order
        to separate BREEZE and report content.
    """
    summary_srting = str()

    if str(report_type) == 'Drug' and len(instance_name) > 0:
        summary_srting = ""

    if str(report_type) == 'Gene' and len(instance_name) > 0:
        if instance_id is not None:
            record_summary = Entrez.esummary(db="gene", id=instance_id)
            record_summary = Entrez.read(record_summary)

            if record_summary[0]["NomenclatureName"]:
                summary_srting += record_summary[0]["NomenclatureName"]
            if record_summary[0]["Orgname"]:
                summary_srting += " [" + record_summary[0]["Orgname"] + "] "
        else:
            summary_srting = "Instance ID is missing!"

    return summary_srting

def dump_project_parameters(project, report):
    dump = '# <----------  Project Details  ----------> \n'
    dump += 'report.author          <- \"%s\"\n' % report.author.username
    dump += 'report.pipeline        <- \"%s\"\n' % report.type
    dump += 'project.name           <- \"%s\"\n' % project.name
    dump += 'project.manager        <- \"%s\"\n' % project.manager
    dump += 'project.pi             <- \"%s\"\n' % project.pi
    dump += 'project.author         <- \"%s\"\n' % project.author
    dump += 'project.collaborative  <- \"%s\"\n' % project.collaborative
    dump += 'project.wbs            <- \"%s\"\n' % project.wbs
    dump += 'project.external.id    <- \"%s\"\n' % project.external_id
    dump += '# <----------  end of Project Details  ----------> \n\n'

    return copy.copy(dump)

def dump_pipeline_config(report_type, query_key):
    dump = ''

    config_path = str(settings.MEDIA_ROOT) + str(report_type.config)
    dump += '# <----------  Pipeline Config  ----------> \n'
    dump += 'query.key          <- \"%s\"  # id of queried RORA instance \n' % query_key
    dump += open(config_path, 'r').read() + '\n'
    dump += '# <------- end of Pipeline Config --------> \n\n\n'

    return copy.copy(dump)

def build_report(report_data, request_data, report_property, sections):
    """ Assembles report home folder, configures DRMAA and R related files
        and spawns a new process for reports DRMAA job on cluster.

    Arguments:
    report_data      -- report info dictionary
    request_data     -- a copy of request object
    report_property  -- report property form
    sections         -- a list of 'Rscripts' db objects

    """
    # 'report_name' - report's headline
    rt = breeze.models.ReportType.objects.get(type=report_data['report_type'])
    report_name = report_data['report_type'] + ' Report' + ' :: ' + report_data['instance_name'] + '  <br>  ' + str(rt.description)

    # This trick is to extract users's names from the form
    # buddies = list()
    # for e in list(report_property.cleaned_data['share']):
    #     buddies.append( str(e) )

    # shared_users = breeze.models.User.objects.filter(username__in=buddies)

    shared_users = aux.extract_users(request_data.POST.get('Groups'), request_data.POST.get('Individuals'))
    insti = breeze.models.UserProfile.objects.get(user=request_data.user).institute_info
    # create initial instance so that we can use its db id
    dbitem = breeze.models.Report(
                type=breeze.models.ReportType.objects.get(type=report_data['report_type']),
                name=str(report_data['instance_name']),
                author=request_data.user,
                progress=0,
                project=breeze.models.Project.objects.get(id=request_data.POST.get('project')),
                institute=insti
                # project=breeze.models.Project.objects.get(name=report_property.cleaned_data['Project'])
            )
    dbitem.save()

    if shared_users:
        dbitem.shared = shared_users

    # define location: that is report's folder name
    path = slugify(str(dbitem.id) + '_' + dbitem.name + '_' + dbitem.author.username)
    loc = str(settings.MEDIA_ROOT) + str("reports/") + path
    dochtml = loc + '/report'
    dbitem.home = str("reports/") + path
    dbitem.save()

    # BUILD R-File
    script_string = 'setwd(\"%s\")\n' % loc
    script_string += 'require( Nozzle.R1 )\n\n'
    script_string += 'path <- \"%s\"\n' % loc
    script_string += 'report_name <- \"%s\"\n' % report_name
    # define a function for exception handler
    script_string += 'failed_fun_print <- function(section_name, error_report){\n'
    script_string += '  Error_report_par  <- newParagraph("<br>", asStrong( "Error Log Details: " ),"<br><br>",asCode(paste(error_report,collapse=""))); \n'
    script_string += '  section_name      <- addTo( section_name, newParagraph( "This section FAILED! Contact the development team... " ), Error_report_par )\n'
    script_string += '  return (section_name)\n}\n\n'

    script_string += dump_project_parameters(dbitem.project, dbitem)
    script_string += dump_pipeline_config(rt, report_data['instance_id'])

    script_string += 'REPORT <- newCustomReport(report_name)\n'

    dummy_flag = False
    for tag in sections:
        secID = 'Section_dbID_' + str(tag.id)
        if secID in request_data.POST and request_data.POST[secID] == '1':
            tree = xml.parse(str(settings.MEDIA_ROOT) + str(tag.docxml))
            script_string += '##### TAG: %s #####\n' % tag.name
            if tag.name == "Import to FileMaker":
                dummy_flag = True

            # source main code segment
            code_path = str(settings.MEDIA_ROOT) + str(tag.code)
            script_string += '# <----------  body  ----------> \n' + open(code_path, 'r').read() + '\n'
            script_string += '# <------- end of body --------> \n'
            # input parameters definition
            script_string += '# <----------  parameters  ----------> \n'
            script_string += gen_params_string(tree, request_data.POST, str(settings.MEDIA_ROOT) + dbitem.home, request_data.FILES)
            script_string += '# <------- end of parameters --------> \n'
            # final step - fire header
            header_path = str(settings.MEDIA_ROOT) + str(tag.header)
            script_string += '# <----------  header  ----------> \n' + open(header_path, 'r').read() + '\n\n'
            script_string += 'new_section <- newSection( section_name )\n'
            script_string += 'tag_section <- tryCatch({section_body(new_section)}, error = function(e){ failed_fun_print(new_section,e) })\n'
            script_string += 'REPORT <- addTo( REPORT, tag_section )\n'
            script_string += '# <------- end of header --------> \n'
            script_string += '##### END OF TAG #####\n\n\n'
            script_string += 'setwd(\"%s\")\n' % loc

        else:  # if tag disabled - do nothing
            pass
    # render report to file
    script_string += '# Render the report to a file\n' + 'writeReport( REPORT, filename=toString(\"%s\"))\n' % dochtml
    script_string += 'system("chmod -R 770 .")'

    # save r-file
    dbitem.rexec.save('script.r', base.ContentFile(script_string))
    dbitem.save()

    # configure shell-file
    config_path = loc + '/sgeconfig.sh'
    config = open(config_path, 'w')

    # config should be executble
    st = os.stat(config_path)
    os.chmod(config_path, st.st_mode | stat.S_IEXEC)

    command = '#!/bin/bash \n' + str(settings.R_ENGINE_PATH) + 'CMD BATCH --no-save ' + str(settings.MEDIA_ROOT) + str(dbitem.rexec)
    config.write(command)
    config.close()

    # open report's folder for others
    st = os.stat(loc)
    os.chmod(loc, st.st_mode | stat.S_IRWXG)

    # submit r-code
    p = Process(target=run_report, args=(dbitem,dummy_flag))
    #print(dbitem)
    #run_report(dbitem,dummy_flag)
    p.start()

    return True
