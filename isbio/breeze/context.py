from django.conf import settings
from breeze.utilities import git_get_branch, git_get_commit


def user_context(request):
    if request.user.is_authenticated():
        is_admin = request.user.groups.filter(name='GEEKS')
        is_auth = True
    else:
        is_admin = False
        is_auth = False

    return {
        'is_local_admin': is_admin,
        'is_authenticated': is_auth,
        'run_mode': settings.RUN_MODE,
        'dev_mode': settings.DEV_MODE,
        'git_branch': git_get_branch(),
        'git_commit': git_get_commit(),
    }


def date_context(_):
    import datetime
    return { 'now': datetime.datetime.now() }
