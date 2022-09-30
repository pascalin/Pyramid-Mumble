import deform.widget
from pyramid.csrf import new_csrf_token
from pyramid.httpexceptions import HTTPSeeOther
from pyramid.security import (
    remember,
    forget,
    NO_PERMISSION_REQUIRED,
)

from pyramid.view import (
    forbidden_view_config,
    view_config,
)

from deform import Form, ValidationFailure, Button
from pyramid_mailer.message import Message
from pyramid_captcha import Captcha

from .. import security
from .. import models
from ..forms import users

import datetime
import itertools
import unidecode


@view_config(route_name='login', renderer='pyramid_mumble:templates/login.jinja2', permission=NO_PERMISSION_REQUIRED)
def login_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

    next_url = request.params.get('next', request.referrer)
    login_url = request.route_url('login')
    if not next_url or next_url == login_url:
        next_url = request.route_url('home')
    form = Form(users.login_schema, buttons=[Button('submit', 'Log in')])
    # form['login']['captcha'].validator = colander.Function(lambda val: Captcha(request).validate(val))

    if 'submit' in request.POST:
        login_schema = users.LoginSchema().bind(captcha=Captcha(request))
        form = Form(login_schema, buttons=[Button('submit', 'Log in')])
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'login_form': e.render(), 'project': project}

        email = appstruct['login']['email']
        password = appstruct['login']['password']

        user = request.dbsession.query(models.MumbleUser).filter_by(email=email).first()
        if user is not None:
            hashed_pw = user.password
            if hashed_pw and security.check_password(password, hashed_pw):
                user.lastlogin = datetime.datetime.utcnow()
                new_csrf_token(request)
                headers = remember(request, user.id)
                return HTTPSeeOther(location=next_url, headers=headers)

        message = 'Failed login'
        request.response.status = 400
        return HTTPSeeOther(request.route_path('failure', action=('login',)))

    return {'login_form': form.render(), 'additions': 0, 'project': project}


@view_config(route_name='recover', renderer='pyramid_mumble:templates/recover.jinja2', permission=NO_PERMISSION_REQUIRED)
def recover_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

    form = Form(users.email_schema, buttons=[Button('submit', 'Recover')])
    # form['captcha'].validator = colander.Function(lambda val: Captcha(request).validate(val))
    # project = "A Triple Helix: metaphor, society, and the science of evolution"

    if 'submit' in request.POST:
        email_schema = users.EmailLoginSchema().bind(captcha=Captcha(request))
        form = Form(email_schema, buttons=[Button('submit', 'Recover')])
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'recover_form': e.render(), 'project': project}

        email = appstruct['email']

        # session = request.session
        # session['email'] = email
        # session['challenge'] = ""

        message = Message(subject="{}: Abnormal activity".format(project),
                          recipients=["david.suarez@ciencias.unam.mx"],
                          body=f"""A failed attempt to recover password for {email} just occurred!""")

        user = request.dbsession.query(models.MumbleUser).filter_by(email=email).first()
        password = security.random_password(hashed=False)
        if user is not None:
            user.password = security.hash_password(password)
            message = Message(subject="{}: Password recovery".format(project),
                              recipients=[email],
                              body=f"""Dear {user.realname}

                              Your password is: {password}""")

        request.mailer.send(
            message)  # Send email challenge if user with email exists otherwise send email to webmaster informing about incident

        return HTTPSeeOther(location=request.route_path('login'))

    return {'recover_form': form.render(), 'additions': 0, 'project': project}


@view_config(route_name='logout')
def logout_view(request):
    next_url = request.route_url('home')
    new_csrf_token(request)
    headers = forget(request)
    return HTTPSeeOther(location=next_url, headers=headers)


@forbidden_view_config(renderer='pyramid_mumble:templates/403.jinja2')
def forbidden_view(exc, request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

    if not request.is_authenticated:
        next_url = request.route_url('login', _query={'next': request.url})
        return HTTPSeeOther(location=next_url)

    request.response.status = 403
    return {'project': project}

@view_config(route_name='settings', renderer='pyramid_mumble:templates/settings.jinja2')
def settings_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

    user = request.identity
    realname = user.realname
    username = user.username
    language = user.language
    timezone = user.timezone

    name_parts = [unidecode.unidecode(part.lower()) for part in realname.split() if len(part) > 2]
    alternatives = ["_".join(choice) for choice in itertools.permutations(name_parts, 2)]
    choices = [('', "---")] + [(x,x) for x in alternatives if x != username and not x.startswith(name_parts[0])]
    # choices = [('', "---")] + [(x, x) for x in alternatives if not x.startswith(name_parts[0])]

    schema = users.MumbleSettingsSchema().bind(
        query=request.dbsession.query(models.MumbleUser),
        alternatives=alternatives,
        username_default=username,
        language_default=language,
        timezone_default = timezone,
    )
    form = Form(schema, buttons=[Button('submit', 'Save settings')])
    # form['username'].validator = colander.OneOf(choices)
    form['username'].widget = deform.widget.SelectWidget(values=choices)

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'settings_form': e.render(), 'project': project}

        user = request.dbsession.query(models.MumbleUser).filter_by(email=request.identity.email).first()
        if user is not None:
            headers = None
            new_language = appstruct['language']
            new_username = appstruct['username']
            new_password = appstruct['password']
            new_timezone = appstruct['timezone']
            # new_public_key = appstruct['publickey']

            if new_language and new_language != user.language:
                user.language = new_language
            if new_username and new_username != username:
                user.username = new_username
            new_hashed_pw = security.hash_password(new_password)
            if new_password and new_hashed_pw != user.password:
                user.password = new_hashed_pw
                new_csrf_token(request)
                headers = remember(request, user.id)
            if new_timezone and new_timezone != user.timezone:
                user.timezone = new_timezone
            # if new_public_key:
            #     user.publickey = new_public_key.encode(),
            return HTTPSeeOther(location=request.path, headers=headers)

    return {'settings_form': form.render(), 'project': project}
