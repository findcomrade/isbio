import copy
import json
import datetime
from django import forms
from django.conf import settings
import xml.etree.ElementTree as xml
import breeze.models, re
from django.db.models import Q
from django.contrib.auth.models import User
from django.template.defaultfilters import default
from decimal import Decimal
import rora as rora
from django.forms import extras
from django.contrib.admin import widgets 
# from bootstrap_toolkit.widgets import BootstrapTextInput, BootstrapPasswordInput

class NewProjectForm(forms.Form):
    project_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': ' Project Name ', })
    )

    project_manager = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': ' Project Manager ', })
    )

    principal_investigator = forms.CharField(
        label=(u'PI'),
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': ' Principal Investigator ', })
    )

    collaborative = forms.BooleanField(
        required=False,
        help_text="Visible by the other users"
    )

    eid = forms.CharField(
        label=(u'External ID'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ' optional ', })
    )

    wbs = forms.CharField(
        label=(u'WBS'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ' optional ', })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 2, 'placeholder': 'optional'}),
        required=False
    )


    def clean_project_name(self):
        project_name = self.cleaned_data.get('project_name')
        try:
            breeze.models.Project.objects.get(name=project_name)
        except breeze.models.Project.DoesNotExist:
            return project_name
        else:
            raise forms.ValidationError("That project name already exists.")

class EditProjectForm(forms.Form):
    eid = forms.CharField(
        label=(u'External ID'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ' optional ', })
    )

    wbs = forms.CharField(
        label=(u'WBS'),
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': ' optional ', })
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 2, 'placeholder': 'optional'}),
        required=False
    )

class GroupForm(forms.Form):
    group_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'placeholder': ' Group Name ', })
    )

    group_team = forms.ModelMultipleChoiceField(
        required=False,
        queryset=breeze.models.User.objects.all(),
        widget=forms.SelectMultiple(
            attrs={'class': 'multiselect', }
        )
    )

    def clean_group_name(self):
        group_name = self.cleaned_data.get('group_name')
        try:
            breeze.models.Group.objects.get(name=group_name)
        except breeze.models.Group.DoesNotExist:
            return group_name
        else:
            raise forms.ValidationError("Group names should be unique")

class EditGroupForm(forms.Form):
    group_team = forms.ModelMultipleChoiceField(
        required=False,
        queryset=breeze.models.User.objects.all(),
        widget=forms.SelectMultiple(
            attrs={'class': 'multiselect', }
        )
    )

class ReportPropsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ReportPropsForm, self).__init__(*args, **kwargs)

        group_list_of_tuples = list()
        users_list_of_tuples = list()

        for ur in breeze.models.User.objects.all():
            users_list_of_tuples.append( tuple((ur.id, ur.username)) )

        for gr in breeze.models.Group.objects.exclude(~Q(author__exact=self.request.user)).order_by("name"):
            group_list_of_tuples.append( tuple((gr.id, gr.name)) )

        share_options = list()
        share_options.append( tuple(( 'Groups', tuple(group_list_of_tuples) )) )
        share_options.append( tuple(( 'Individual Users', tuple(users_list_of_tuples) )) )

        self.fields["project"] = forms.ModelChoiceField(
            queryset=breeze.models.Project.objects.exclude(~Q(author__exact=self.request.user) & Q(collaborative=False)).order_by("name")
        )

        self.fields["Share"] = forms.MultipleChoiceField(
            required=False,
            choices=share_options,
            #queryset=breeze.models.User.objects.all(),
            widget=forms.SelectMultiple(
                attrs={'class': 'multiselect', }
            )
        )


class ReportPropsFormOld(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request")
        super(ReportPropsForm, self).__init__(*args, **kwargs)
        self.fields["project"] = forms.ModelChoiceField(
            queryset=breeze.models.Project.objects.exclude(~Q(author__exact=self.request.user) & Q(collaborative=False)).order_by("name")
        )

    class Meta:
        model = breeze.models.Report
        fields = ('shared',)


class RegistrationForm(forms.ModelForm):
    def __init__(self, *args, **kw):
        super(forms.ModelForm, self).__init__(*args, **kw)
        self.fields.keyOrder = [
            'username',
            'email',
            'first_name',
            'last_name',
            'fimm_group',
            'password',
            'password1']

    username = forms.CharField(label=(u'User Name'))
    email = forms.EmailField(label=(u'Email Address'))
    password = forms.CharField(label=(u'Password'), widget=forms.PasswordInput(render_value=False))
    password1 = forms.CharField(label=(u'Verify Password'), widget=forms.PasswordInput(render_value=False))

    class Meta:
        model = breeze.models.UserProfile
        exclude = ('user', 'logo')

    def clean_username(self):
        username = self.cleaned_data['username']
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        else:
            raise forms.ValidationError("That user name is already taken.")

    def clean(self):
        password = self.cleaned_data.get('password', None)
        password1 = self.cleaned_data.get('password1', None)
        if password and password1 and (password == password1):
            return self.cleaned_data
        else:
            raise forms.ValidationError("The passowords did not match. Please try again.")

class PersonalInfo(forms.Form):
    first_name = forms.CharField(
        max_length=55,
        widget=forms.TextInput(attrs={'placeholder': ' First Name ', })
    )
    last_name = forms.CharField(
        max_length=55,
        widget=forms.TextInput(attrs={'placeholder': ' Last Name ', })
    )
    email = forms.EmailField(
        max_length=75,
        widget=forms.TextInput(attrs={'placeholder': ' first.last@helsinki.fi ', })
    )
    


class PatientInfo(forms.Form):
    def __init__(self, *args, **kwargs):

        super(PatientInfo, self).__init__(*args, **kwargs)
        
        
        self.fields['patient_id'] = forms.IntegerField(
            required=False,
            label = "Patient ID",
            widget = forms.TextInput(attrs={'placeholder': ' ID ', 'readonly': True, })
        )
    
        self.fields['identifier'] = forms.CharField(
            max_length = 75,
            label = "Indentifier",
            widget = forms.TextInput(attrs={'placeholder': ' Indentifier ', })
        )
        
        self.fields['source'] = forms.CharField(
            max_length = 75,
            label = "Source",
            widget = forms.TextInput(attrs={'placeholder': ' Source ', })
        )
    
        self.fields['description'] = forms.CharField(
            required=False,
            max_length = 7500,
            label = "Description",
            widget = forms.Textarea(attrs={'cols': 15, 'rows': 2, 'placeholder': 'Description'})
        )
        
        organism_list = list()
        organisms = json.loads(rora.organism_data()[0])
        for ID, name in zip(organisms[0]['ORGANISM_ID'], organisms[1]['DESCRIPTION']):
            organism_list.append(tuple((ID, name)))
        #print(organisms)
        self.fields['organism'] = forms.ChoiceField(
            required=False,
            choices=organism_list,
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        sex_list = list()
        sex = json.loads(rora.sex_data()[0])
       
        sex_list.append(tuple((0, 'Unkown')))
        for ID, name in zip(sex[0]['SEX_ID'], sex[1]['DESCRIPTION']):
            sex_list.append(tuple((ID, name)))
            
        self.fields['sex'] = forms.ChoiceField(
            required=False,
            choices=sex_list,
            #initial=0,
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        #print(organism_list[0][0])
    
        self.fields['birthdate'] = forms.DateField(
            widget = widgets.AdminDateWidget(),
            initial = datetime.date.today()
        )
        
        
class ScreenGroupInfo(forms.Form):
    def __init__(self, *args, **kwargs):

        super(ScreenGroupInfo, self).__init__(*args, **kwargs)
        # screen group info
        screen_list = list()
        screen = json.loads(rora.getAllScreens()[0])
        for ID, name in zip(screen[0]['PK_SCREEN_ID'], screen[1]['BREEZE_ALIAS']):
            screen_list.append(tuple((ID, name)))
            
        self.fields['dst'] = forms.MultipleChoiceField(
            required=False,
            choices=screen_list,
            label='Group Content',
            widget=forms.SelectMultiple(
                attrs={'class': 'multiselect', }
            )
        )
    

class ScreenInfo(forms.Form):
    def __init__(self, *args, **kwargs):

        super(ScreenInfo, self).__init__(*args, **kwargs)

        self.fields['screen_id'] = forms.IntegerField(
            #required=False,
            label = "Sreen ID",
            widget = forms.TextInput(attrs={'placeholder': ' ID ', 'readonly': True, })
        )
        
        self.fields['identifier'] = forms.CharField(
            max_length = 75,
            label = "Indentifier",
            widget = forms.TextInput(attrs={'placeholder': ' Indentifier ', 'readonly': True})
        )
        
        self.fields['description'] = forms.CharField(
            required=False,
            max_length = 7500,
            label = "Description",
            widget = forms.Textarea(attrs={'cols': 15, 'rows': 2, 'placeholder': 'Description', 'readonly':                                         True})
        )
        
        self.fields['source_id'] = forms.CharField(
            required=False,
            max_length = 75,
            label = "Source ID",
            widget = forms.TextInput(attrs={'placeholder': ' Source ID', 'readonly': True})
        )
        
        self.fields['source'] = forms.CharField(
            max_length = 75,
            label = "Source",
            widget = forms.TextInput(attrs={'placeholder': ' Source ', 'readonly': True})
        )
    
        self.fields['protocol'] = forms.CharField(
            required=False,
            max_length = 75,
            label = "Protocol",
            widget = forms.TextInput(attrs={'placeholder': ' Protocol ', 'readonly': True})
        )
        
        patient_list = list()
        patients = json.loads(rora.get_all_patient()[0])
        for ID, name in zip(patients[0]['PK_ENTITY_ID'], patients[1]['IDENTIFIER']):
            patient_list.append(tuple((ID, name)))
            
        self.fields['patient'] = forms.ChoiceField(
            required=False,
            choices=patient_list,
            label='Patient',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        self.fields['alias'] = forms.CharField(
            #required=False,
            max_length = 75,
            label = "Breeze Alias",
            widget = forms.TextInput(attrs={'placeholder': ' Breeze Alias '})
        )
        
        # sample type
        st_list = list()
        st = json.loads(rora.sample_type()[0])
        for ID, name in zip(st[0]['SAMPLE_TYPE_ID'], st[1]['DESCRIPTION']):
            st_list.append(tuple((ID, name)))
            
        self.fields['st'] = forms.ChoiceField(
            required=False,
            choices=st_list,
            label='Sample Type',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # disease sub type
        dst_list = list()
        dst = json.loads(rora.disease_sub_type()[0])
        for ID, name in zip(dst[0]['DISEASE_SUB_TYPE_ID'], dst[1]['DESCRIPTION']):
            dst_list.append(tuple((ID, name)))
        self.fields['dst'] = forms.ChoiceField(
            required=False,
            choices=dst_list,
            label='Disease Sub Type',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        # media type 
        mt_list = list()
        
        mt = json.loads(rora.media_type()[0])
        for ID, name in zip(mt[0]['MEDIA_TYPE_ID'], mt[1]['DESCRIPTION']):
            mt_list.append(tuple((ID, name)))
        self.fields['mt'] = forms.ChoiceField(
            required=False,
            choices=mt_list,
            label='Media Type',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        # histology
        history_list = list()
        
        history = json.loads(rora.histology()[0])
        for ID, name in zip(history[0]['HISTOLOGY_ID'], history[1]['DESCRIPTION']):
            history_list.append(tuple((ID, name)))
        
        self.fields['histology'] = forms.ChoiceField(
            required=False,
            choices=history_list,
            label='Histology',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # disease state
        d_state_list = list()
        d_state = json.loads(rora.disease_state_data()[0])
        for ID, name in zip(d_state[0]['DISEASE_STATE_ID'], d_state[1]['DESCRIPTION']):
            d_state_list.append(tuple((ID, name)))
    
        self.fields['dstate'] = forms.ChoiceField(
            required=False,
            choices=d_state_list,
            label='Disease State',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # experiment type
        et_list = list()
        et = json.loads(rora.experiment_type_data()[0])

        for ID, name in zip(et[0]['EXPERIMENT_TYPE_ID'], et[1]['DESCRIPTION']):
            et_list.append(tuple((ID, name)))

        self.fields['et'] = forms.ChoiceField(
            required=False,
            choices=et_list,
            label='Experiment Type',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # plate count
        
        self.fields['plate_count'] = forms.IntegerField(
            #required=False,
            label = "Plate Count",
            widget = forms.TextInput(attrs={'placeholder': ' Plate Count '})
        )
        
        # disease grade
        
        dg_list = list()
        dg = json.loads(rora.disease_grade_data()[0])

        for ID, name in zip(dg[0]['DISEASE_GRADE_ID'], dg[1]['DESCRIPTION']):
            dg_list.append(tuple((ID, name)))

        self.fields['dg'] = forms.ChoiceField(
            required=False,
            choices=dg_list,
            label='Disease Grade',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # disease stage
        disease_stage_list = list()
        disease_stage = json.loads(rora.disease_stage_data()[0])

        for ID, name in zip(disease_stage[0]['DISEASE_STAGE_ID'], disease_stage[1]['DESCRIPTION']):
            disease_stage_list.append(tuple((ID, name)))

        self.fields['disease_stage'] = forms.ChoiceField(
            required=False,
            choices=disease_stage_list,
            label='Disease Stage',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # read out
        read_out_list = list()
        read_out = json.loads(rora.read_out_data()[0])

        for ID, name in zip(read_out[0]['SCREEN_READOUT_ID'], read_out[1]['DESCRIPTION']):
            read_out_list.append(tuple((ID, name)))

        self.fields['read_out'] = forms.ChoiceField(
            required=False,
            choices=read_out_list,
            label='Screen Read Out',
            #initial=organism_list[0][0],
            widget=forms.Select(
                attrs={'class': 'multiselect', }
            )
        )
        
        # create date
        
        self.fields['createdate'] = forms.DateField(
            label = 'Create Date',
            widget = widgets.AdminDateWidget(),
            initial = datetime.date.today()
        )
    
    
    
    


    

class LoginForm(forms.Form):
    user_name = forms.CharField(
        max_length=30,
        label="",
        widget=forms.TextInput(
             attrs={
             'placeholder': 'user name...',
             'class': 'input-medium',
         }),
    )
    password = forms.CharField(
        max_length=30,
        label="",
        widget=forms.PasswordInput(attrs={
            'placeholder': 'password...',
            'class': 'input-small',
        })
    )

class NewScriptDialog(forms.Form):
    name = forms.CharField(
        max_length=35,
        label=(u'Script Name')
    )

    inline = forms.CharField(
        max_length=150,
        label="Inline Description",
        widget=forms.Textarea(
             attrs={
                'class': 'input-large',
                'rows': 1
         }),
    )

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            breeze.models.Rscripts.objects.get(name=name)
        except breeze.models.Rscripts.DoesNotExist:
            return name
        else:
            raise forms.ValidationError("That script name is already taken.")

class NewRepTypeDialog(forms.ModelForm):
    class Meta:
        model = breeze.models.ReportType
        fields = ('type', 'description', 'search', 'access')


class BasicJobForm(forms.Form):
    def __init__(self, user, edit, *args, **kwargs):
        self._user = user
        self._edit = edit
        super(BasicJobForm, self).__init__(*args, **kwargs)

    job_name = forms.CharField(
        max_length=35,
    )
    job_details = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 15, 'rows': 2, 'placeholder': 'optional'}),
        required=False
    )


    def clean_job_name(self):
        job_name = self.cleaned_data.get('job_name')
        try:
            exst = breeze.models.Jobs.objects.filter(juser__exact=self._user).get(jname=job_name)
        except breeze.models.Jobs.DoesNotExist:
            return job_name
        else:
            if str(exst) == str(self._edit):
                return job_name
            else:
                raise forms.ValidationError("That job name already exists.")

class CustomForm(forms.Form):
    def setFields(self, kwds):
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

### Forms for script submissions ###
class ScriptBasics(forms.Form):
    def __init__(self, edit, *args, **kwargs):
        self._edit = edit
        super(ScriptBasics, self).__init__(*args, **kwargs)

    name = forms.CharField(
        max_length=35,
        widget=forms.TextInput(
             attrs={
                'class': 'input-large',
         }),
    )

    inline = forms.CharField(
        max_length=150,
        label="Inline Description",
        widget=forms.Textarea(
             attrs={
                'class': 'input-xxlarge',
                'rows': 3
         }),
    )

    def clean_name(self):
        name = self.cleaned_data['name']
        try:
            exst = breeze.models.Rscripts.objects.get(name=name)
        except breeze.models.Rscripts.DoesNotExist:
            return name
        else:
            if str(exst) == str(self._edit):
                return name
            else:
                raise forms.ValidationError("That script name is already taken.")

class ScriptDescription(forms.Form):
    description = forms.CharField(
        max_length=5500,
        label="",
        widget=forms.Textarea(
             attrs={
                'class': 'input-xxlarge',
                'rows': 11
         }),
    )

class ScriptAttributes(forms.ModelForm):
    class Meta:
        model = breeze.models.Rscripts
        fields = ('author', 'category', 'draft', 'istag', 'report_type')

class ScriptLogo(forms.Form):
    logo = forms.FileField(label=(u''))

### old implementation ###
class ScriptMainForm(forms.ModelForm):
    class Meta:
        model = breeze.models.Rscripts
        fields = ('name', 'inln', 'category', 'details', 'logo')

class ScriptSources(forms.Form):
    code = forms.FileField()
    header = forms.CharField(
        widget=forms.Textarea(attrs={'cols': 55, 'rows': 15, }),
        help_text='Header',
    )

class AddBasic(forms.Form):
    TYPE_OPT = (
        (u'NUM', u'Numeric'),
        (u'CHB', u'Check Box'),
        (u'DRP', u'Drop Down'),
        (u'RAD', u'Radio'),
        (u'TEX', u'Text'),
        (u'TAR', u'Text Area'),
        (u'FIL', u'File Upload'),
        (u'HED', u'Heading'),
    )

    def drop_titles(self, *args, **kwargs):
        self.fields['inline_var'].label = ""
        self.fields['comment'].label = ""

    inline_var = forms.CharField(max_length=35,
        widget=forms.TextInput(attrs={'class': 'input-mini'})
        )
    type = forms.CharField(widget=forms.HiddenInput(), required=False)
    comment = forms.CharField(max_length=55,
        widget=forms.TextInput(attrs={'class': 'input-xlarge'})
        )
#    default = forms.CharField(max_length=35,
#        widget=forms.TextInput(attrs={'class': 'input-mini'}),
#        required=False
#        )

class AddOptions(forms.Form):
    def drop_titles(self, *args, **kwargs):
        self.fields['options'].label = ""

    options = forms.CharField(max_length=55,
        widget=forms.TextInput(attrs={'class': 'input-xlarge'}))

class AddDatasetSelect(forms.Form):
    options = forms.ModelMultipleChoiceField(queryset=breeze.models.DataSet.objects.all(), widget=forms.CheckboxSelectMultiple())


class AddTemplateInput(forms.Form):
    """
        This control is for uploading template
        inpit file which can be downloaded from BREEZE beforehand
    """
    options = forms.ModelChoiceField(queryset=breeze.models.InputTemplate.objects.all())

class HiddenForm(forms.Form):
    next = forms.CharField(widget=forms.HiddenInput())
    curr = forms.CharField(widget=forms.HiddenInput())


def xml_from_form(form_g, form_d, form_s):
    root = xml.Element('rScript')
    root.attrib['name'] = form_g.cleaned_data['name']
    inline = xml.Element('inline')
    inline.text = form_g.cleaned_data['inln']
    root.append(inline)
    details = xml.Element('details')
    details.text = form_g.cleaned_data['details']
    root.append(details)
    status = xml.Element('status')
    status.attrib['val'] = 'none'
    root.append(status)
    input_array = xml.Element('inputArray')

    for key in form_d:
        common_form = form_d[key][0]
        ipt = xml.Element('inputItem')
        ipt.attrib['type'] = common_form.cleaned_data['type']
        ipt.attrib['rvarname'] = common_form.cleaned_data['inline_var']
        ipt.attrib['comment'] = common_form.cleaned_data['comment']
        ipt.attrib['val'] = ""

        if common_form.cleaned_data['type'] == 'TPL':
            extra_form = form_d[key][1]
            ipt.attrib['default'] = str(extra_form.cleaned_data['options'])
        else:
            ipt.attrib['default'] = ""

        if common_form.cleaned_data['type'] == 'DRP' or common_form.cleaned_data['type'] == 'RAD':
            extra_form = form_d[key][1]  # [0] form is the common one
            altar = xml.Element('altArray')
            for opt in str(extra_form.cleaned_data['options']).split():
                altit = xml.Element('altItem')
                altit.text = opt
                altar.append(altit)
            ipt.append(altar)

        if common_form.cleaned_data['type'] == 'DTS':
            extra_form = form_d[key][1]
            altar = xml.Element('altArray')
            for opt in extra_form.cleaned_data['options']:
                altit = xml.Element('altItem')
                altit.text = str(opt)
                altar.append(altit)
            ipt.append(altar)

        input_array.append(ipt)

    root.append(input_array)

    # newxml = open("/home/comrade/Projects/fimm/tmp/test.xml", 'w')
    newxml = open(str(settings.TEMP_FOLDER) + 'test.xml', 'w')
    xml.ElementTree(root).write(newxml)
    newxml.close()
    return newxml

def form_from_xml(xml, req=None, init=False, usr=None):
    input_array = xml.getroot().find('inputArray')

    if req:
        custom_form = CustomForm(req.POST, req.FILES)
    elif init:
        custom_form = CustomForm(req.POST, req.FILES)
    else:
        custom_form = CustomForm()


    if input_array != None:
        for input_item in input_array:
            if input_item.tag == "inputItem":

                try:
                    if input_item.attrib["optional"] == '1':
                        optional_prop = False
                    else:
                        optional_prop = True
                except:
                    optional_prop = True

                try:
                    help_line = input_item.attrib["help"]
                except:
                    help_line = ''

                if  input_item.attrib["type"] == "NUM":  # numeric input
                    # protect empty MAX and MIN limits
                    if input_item.attrib["max"]:
                        max_decimal = Decimal(input_item.attrib["max"])
                    else:
                        max_decimal = None

                    if input_item.attrib["min"]:
                        min_decimal = Decimal(input_item.attrib["min"])
                    else:
                        min_decimal = None

                    custom_form.fields[input_item.attrib["comment"]] = forms.DecimalField(
                            initial=input_item.attrib["val"],
                            max_value=max_decimal,
                            min_value=min_decimal,
                            required=optional_prop,
                            help_text=help_line
                    )

                elif input_item.attrib["type"] == "TEX":  # text box
                    custom_form.fields[input_item.attrib["comment"]] = forms.CharField(
                            initial=input_item.attrib["val"],
                            max_length=100,
                            required=optional_prop,
                            help_text=help_line,
                            widget=forms.TextInput(attrs={'type': 'text', })
                    )
                elif input_item.attrib["type"] == "TAR":  # text area
                    custom_form.fields[input_item.attrib["comment"]] = forms.CharField(
                            initial=input_item.attrib["val"],
                            required=optional_prop,
                            help_text=help_line,
                            widget=forms.Textarea(
                                attrs={
                                    'cols': 15,
                                    'rows': 3,
                                }
                                                  )
                                                                   )

                elif input_item.attrib["type"] == "CHB":  # check box
                    checked = False
                    if input_item.attrib["val"] == "true":
                        checked = True
                    custom_form.fields[input_item.attrib["comment"]] = forms.BooleanField(
                            required=False,
                            initial=checked,
                            help_text=help_line
                    )

                elif input_item.attrib["type"] == "DRP":  # drop down list
                    drop_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        drop_options = drop_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.ChoiceField(
                            choices=drop_options,
                            initial=input_item.attrib["val"],
                            help_text=help_line
                    )

                elif input_item.attrib["type"] == "DTS":  # custom dataset (drop down list control)
                    drop_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        drop_options = drop_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.ChoiceField(
                            choices=drop_options,
                            initial=input_item.attrib["val"],
                            help_text=help_line
                    )

                elif input_item.attrib["type"] == "RAD":  # radio buttons
                    radio_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        radio_options = radio_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.ChoiceField(
                            initial=input_item.attrib["val"],
                            widget=forms.RadioSelect(attrs={'value': input_item.attrib["default"]}),
                            choices=radio_options,
                            help_text=help_line
                    )

                elif input_item.attrib["type"] == "FIL" or input_item.attrib["type"] == "TPL":  # file upload field
                    custom_form.fields[input_item.attrib["comment"]] = forms.FileField(
                            # initial=input_item.attrib["val"],
                            required=optional_prop,
                            help_text=help_line,
                            widget=forms.ClearableFileInput(
                                attrs={
                                       'class': input_item.attrib["type"],
                                       'which': input_item.attrib["default"],
                                }
                                                            )
                                                                                       )
                elif input_item.attrib["type"] == "MLT":  # multiple select
                    mult_options = tuple()

                    for alt in input_item.find('altArray').findall('altItem'):
                        mult_options = mult_options + ((alt.text, alt.text),)

                    custom_form.fields[input_item.attrib["comment"]] = forms.MultipleChoiceField(
                            initial=re.split(',', input_item.attrib["val"]),
                            help_text=help_line,
                            choices=mult_options
                    )

                # Dotmatix samples control
                elif input_item.attrib["type"] == "DTM_SAMPLES":  # custom dataset (multiple select)

                    group_list_of_tuples = list()
                    sample_list_of_tuples = list()

                    # push r-code here to populate dtm_samples
                    group_list_of_tuples = rora.get_dtm_screen_groups()
                    sample_list_of_tuples = rora.get_dtm_screens()

                    dtm_options = list()
                    dtm_options.append( tuple(( 'Groups', tuple(group_list_of_tuples) )) )
                    dtm_options.append( tuple(( 'Individual Screens', tuple(sample_list_of_tuples) )) )


                    custom_form.fields[input_item.attrib["comment"]] = forms.MultipleChoiceField(
                            choices=dtm_options,
                            initial=input_item.attrib["val"],
                            required=optional_prop,
                            help_text=help_line,
                            widget=forms.SelectMultiple(attrs={'class':'dotmatix_samples'})
                    )

                elif input_item.attrib["type"] == "HED":  # section header
                    pass
                else:
                    pass
            elif input_item.tag == "subSection":
                print "section"
            else:
                pass


    return custom_form

def create_report_sections(sections, req=None):
    """ Creates a list of sections content for report overview page.

    Arguments:
    sections      -- list of 'Rscripts' db objects

    """
    sdata = dict()
    section_lst = list()

    for item in sections:
        tree = xml.parse(str(settings.MEDIA_ROOT) + str(item.docxml))
        sdata['id'] = item.id
        sdata['inline'] = str(item.inln)
        sdata['name'] = str(item.name)
        sdata['form'] = form_from_xml(xml=tree, usr=req.user)
        section_lst.append( dict(sdata) )

    return section_lst

def validate_report_sections(sections, req):
    """ Validate only checked (marked) report sections.

    Arguments:
    sections    -- list of 'Rscripts' db objects
    req         -- a copy of request

    """
    sdata = dict()
    section_lst = list()

    for item in sections:
        tree = xml.parse(str(settings.MEDIA_ROOT) + str(item.docxml))
        sdata['id'] = item.id
        sdata['inline'] = str(item.inln)
        sdata['name'] = str(item.name)

        # we want to validate only those sections
        # that have been enabled by user
        secID = 'Section_dbID_' + str(item.id)
        if secID in req.POST and req.POST[secID] == '1':
            sdata['form'] = form_from_xml(xml=tree, req=req, usr=req.user)
            sdata['isvalid'] = sdata['form'].is_valid()
        else:
            sdata['form'] = form_from_xml(xml=tree, usr=req.user)
            sdata['isvalid'] = True

        section_lst.append( dict(sdata) )

    return section_lst

def check_validity(sections):
    """ Reports whether all sections are valid or not

    Arguments:
    sections    -- a list of dict()

    """
    for item in sections:
        if not item['isvalid']:
            return False

    return True

def job_summary(xml):
    pass
