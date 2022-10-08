import deform.widget
from pyramid.csrf import new_csrf_token
from pyramid.httpexceptions import HTTPSeeOther, HTTPNotFound
from pyramid.response import Response, FileResponse
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
import tempfile
import logging
import os

@view_config(route_name='login', renderer='pyramid_mumble:templates/login.jinja2', permission=NO_PERMISSION_REQUIRED)
def login_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

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
            return {'login_form': e.render(), 'project': project, 'website': website}

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

    return {'login_form': form.render(), 'additions': 0, 'project': project, 'website': website}


@view_config(route_name='recover', renderer='pyramid_mumble:templates/recover.jinja2', permission=NO_PERMISSION_REQUIRED)
def recover_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

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
            return {'recover_form': e.render(), 'project': project, 'website': website}

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
            message = Message(subject=f"{project}: Password recovery",
                              recipients=[email],
                              body=f"""Dear {user.realname},
                              you, or someone else, asked for your password to be recovered at the {project}'s conference site.
                              
                              Your password is the following:
                               
                               {password}
                                
                               You can use it to log in through following link: {request.route_url('login')}
                              
                              Sincerely,
                              the friendly webmaster of {project}.
                              """,
                              html=f"""<p>Dear <strong>{user.realname}</strong>,<br>
                              you, or someone else, asked for your password to be recovered at the {project}'s conference site.</p>
                              <p>Your password is the following:<br>
                               <strong>{password}</strong><br>
                                and you can use it to log in through
                               the following link: <a href="{request.route_url('login')}">{request.route_url('login')}</a></p>
                              <p>Sincerely,<br>
                              the friendly webmaster of {project}.</p>
                              """
                              )

        request.mailer.send(
            message)  # Send email challenge if user with email exists otherwise send email to webmaster informing about incident

        return HTTPSeeOther(location=request.route_path('login'))

    return {'recover_form': form.render(), 'additions': 0, 'project': project, 'website': website}


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
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    if not request.is_authenticated:
        next_url = request.route_url('login', _query={'next': request.url})
        return HTTPSeeOther(location=next_url)

    request.response.status = 403
    return {'project': project, 'website': website}

@view_config(route_name='settings', renderer='pyramid_mumble:templates/settings.jinja2')
def settings_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    user = request.identity
    realname = user.realname
    username = user.username
    language = user.language
    timezone = user.timezone

    name_parts = [unidecode.unidecode(part.lower()) for part in realname.split() if len(part) > 2]
    alternatives = ["_".join(choice) for choice in itertools.permutations(name_parts, 2)]
    choices = [('', "---")] + [(x,x) for x in alternatives if x != username and not x.startswith(name_parts[0])]
    # choices = [('', "---")] + [(x, x) for x in alternatives if not x.startswith(name_parts[0])]

    schema = users.UserSettingsSchema().bind(
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
            return {'settings_form': e.render(), 'project': project, 'website': website}

        user = request.dbsession.query(models.MumbleUser).filter_by(email=request.identity.email).first()
        if user is not None:
            headers = None
            new_language = appstruct['language']
            new_username = appstruct['username']
            new_password = appstruct['password']
            new_timezone = appstruct['timezone']

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
            return HTTPSeeOther(location=request.path, headers=headers)

    return {'settings_form': form.render(), 'project': project, 'website': website}


@view_config(route_name='mumble_settings', renderer='pyramid_mumble:templates/mumble_settings.jinja2')
def mumble_settings_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    user = request.identity
    email = user.email
    username = user.username

    # name_parts = [unidecode.unidecode(part.lower()) for part in realname.split() if len(part) > 2]
    # alternatives = ["_".join(choice) for choice in itertools.permutations(name_parts, 2)]
    # choices = [('', "---")] + [(x,x) for x in alternatives if x != username and not x.startswith(name_parts[0])]
    # choices = [('', "---")] + [(x, x) for x in alternatives if not x.startswith(name_parts[0])]

    # schema = users.UserSettingsSchema().bind(
    #     query=request.dbsession.query(models.MumbleUser),
    #     alternatives=alternatives,
    #     username_default=username,
    #     language_default=language,
    #     timezone_default = timezone,
    # )
    # form = Form(schema, buttons=[Button('submit', 'Save settings')])
    # # form['username'].validator = colander.OneOf(choices)
    # form['username'].widget = deform.widget.SelectWidget(values=choices)

    form = Form(users.MumbleSettingsSchema(), buttons=[Button('submit', 'Save settings')])
    appstruct = {
        'email': request.identity.email,
    }

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'mumble_form': e.render(), 'project': project, 'website': website}

        user = request.dbsession.query(models.MumbleUser).filter_by(email=request.identity.email).first()
        if user is None:
            raise HTTPNotFound()
        dest_dir = os.path.join(request.registry.settings['mumble.storage'], user.email)
        new_privkey = appstruct['privkey']

        if new_privkey:
            logging.warning(f"Received {new_privkey} to store")
            p12 = new_privkey['fp']
            user.certificate, user.privkey = security.x509.import_pkcs12(data=p12.read(), dest_dir=dest_dir)
            if request.context.mumble.is_alive():
                request.context.mumble.stop()
        return HTTPSeeOther(location=request.path)

    return {'mumble_form': form.render(appstruct), 'project': project, 'website': website}


@view_config(route_name="mumble_export")
def mumble_get_key(request):
    user = request.identity
#    response = Response(content_type='application/x-pkcs12')
    with tempfile.NamedTemporaryFile(prefix="PKCS12_Export_%s" % datetime.datetime.now(),
                            suffix='.p12', delete=False) as f:
        f.write(security.x509.export_pkcs12(user))
        # this is where I usually put stuff in the file
        # response.app_iter = f
        # response.headers['Content-Disposition'] = (f"attachment; filename={user.username}.p12")
        # return response
    response = FileResponse(
        f.name,
        request=request,
        content_type='application/x-pkcs12'
    )
    response.headers['Content-Disposition'] = (f"attachment; filename={user.username}.p12")
    return response