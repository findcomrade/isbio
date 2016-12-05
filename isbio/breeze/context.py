from django.conf import settings


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
        'git_branch': settings.CURRENT_GIT_BRANCH,
        'git_commit': settings.CURRENT_GIT_COMMIT,
    }


def date_context(_):
    import datetime
    return { 'now': datetime.datetime.now() }
