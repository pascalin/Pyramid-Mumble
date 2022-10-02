from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPSeeOther, HTTPNotFound
from pyramid.security import NO_PERMISSION_REQUIRED
from sqlalchemy.exc import SQLAlchemyError
from deform import Form, ValidationFailure, Button
import colander
from pyramid_mailer.message import Message
from pyramid_captcha import Captcha
from .. import security
from .. import models
from ..forms import users

import datetime, pytz, pycountry, os


@view_config(route_name='home', renderer='pyramid_mumble:templates/home.jinja2', permission=NO_PERMISSION_REQUIRED)
def main_view(request):
    meeting = query = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    tz_mexico = pytz.timezone('America/Mexico_City')
    start_time = datetime.datetime(2022, 10, 3, 9, 0, 0, 0, tzinfo=tz_mexico)
    now = datetime.datetime.now(tz_mexico)
    if now < start_time:
        remaining = start_time - now
    else:
        remaining = datetime.timedelta(0)
    try:
        query = request.dbsession.query(models.MumbleUser)
        users = query.all()
    except SQLAlchemyError:
        return Response(db_err_msg, content_type='text/plain', status=500)
    return {'users': len(users), 'days': remaining.days, 'speakers': 39,
            'project': project, 'website': website}


@view_config(route_name='signin', permission=NO_PERMISSION_REQUIRED)
def signin_view(request):
    return HTTPSeeOther(location=request.route_path("signup"))


@view_config(route_name='signup', renderer='pyramid_mumble:templates/signin.jinja2', permission=NO_PERMISSION_REQUIRED)
def signup_view(request):
    if request.is_authenticated:
        raise HTTPSeeOther(request.route_path("profile", uid=request.identity.id))

    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    form = Form(users.user_schema, buttons=[Button('submit','Sign in')])
    # form['user']['captcha'].validator = colander.Function(lambda val: Captcha(request).validate(val) is None)

    if 'submit' in request.POST:
        user_schema = users.UserSchema().bind(captcha=Captcha(request), query=request.dbsession.query(models.MumbleUser))
        form = Form(user_schema, buttons=[Button('submit', 'Sign in')])
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'register_form': e.render(), 'project': project, 'website': website}

        realname = appstruct['user']['realname']
        email = appstruct['user']['email']
        # name_parts = [part.lower() for part in realname.split()]
        # username = f"{name_parts[-1]}_{name_parts[0]}"
        password = security.random_password(hashed=False)
        hashed_password = security.hash_password(password)

        user = models.MumbleUser(
            realname=realname,
            # username=username,
            organization=appstruct['user']['organization'],
            country=appstruct['user']['country'],
            state=appstruct['user']['state'],
            email=appstruct['user']['email'],
            language=appstruct['user']['language'],
            password=hashed_password,
        )
        dest_dir = os.path.join(request.registry.settings['mumble.storage'], email)
        parent_dir = "/".join(os.path.split(dest_dir)[:-1])
        if not os.path.isdir(dest_dir) and os.path.exists(parent_dir):
            os.makedirs(dest_dir)

        user.certificate, user.privkey = security.x509.generate_selfsigned_cert(user, dest_dir=dest_dir)
        request.dbsession.add(user)

        # project = "A Triple Helix: metaphor, society, and the science of evolution"
        message = Message(subject="{}: Successful registration".format(project),
                          recipients=[appstruct['user']['email']],
                          body=f"""Dear {realname},
                          you have been successfully registered to {project}.
                          
                          The workshop will take place from October 3-7.<br>Briefly, you will receive a confirmation
                           email with more details for logging into the conference website and to make some preparations
                           in order to enhance your interactions during the conference.
                                              
                           To access the conference site enter: {request.route_url('login')}
                           
                           Employing the following password:
                            
                            {password}
                          """,
                          html=f"""<p>Dear <strong>{realname}</strong>,<br>
                          you have been successfully registered to {project}.</p>
                          <p>The workshop will take place from October 3-7.<br>Briefly, you will receive a confirmation
                           email with more details for logging into the conference website and to make some preparations
                           in order to enhance your interactions during the conference.</p>
                           <p>To access the conference site enter: <a href="{request.route_url('login')}">{request.route_url('login')}</a><br>
                           Employing the following password:<br>
                            <strong>{password}</strong></p>
                           """,
                          )

        request.mailer.send(message)

        session = request.session
        session['realname'] = realname

        return HTTPSeeOther(location=request.route_path("success_signin"))

    return {'register_form': form.render(), 'additions': 0, 'project': project, 'website': website}


@view_config(route_name='captcha', permission=NO_PERMISSION_REQUIRED)
def captcha_generate_view(request):
    captcha_id = request.matchdict['captcha_id']
    response = Captcha(request, length=4).generate()
    response.headers["Cache-Control"] = "no-cache"
    return response


@view_config(route_name='success_signin', renderer='pyramid_mumble:templates/success.jinja2', permission=NO_PERMISSION_REQUIRED)
def success_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    session = request.session
    if 'realname' in session and not request.is_authenticated:
        realname = session['realname']
        del session['realname']

        return {
            'realname': realname,
            'action': "signed in",
            'project': project, 'website': website,
            'message': """<p>The workshop will take place from <strong>October 3 to October 7</strong>.</p><p>Briefly, you will receive a confirmation
             email with more details for logging into the conference website and to make some preparations in order to
             enhance your interactions during the conference.</p>"""
        }
    else:
        return HTTPSeeOther(request.route_path("home"))


@view_config(route_name='failure', renderer='pyramid_mumble:templates/failure.jinja2', permission=NO_PERMISSION_REQUIRED)
def failure_view(request):
    action = request.matchdict['action']
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    if 'login' in action:
        message = """<p>Your combination of email and password is not correct. If you are already registered, 
        please check that you have written your password correctly. Otherwise, please register or contact us by 
        email. """
    else:
        return HTTPSeeOther(request.route_path("home"))

    return {
        'action': action[0],
        'message': message,
        'project': project, 'website': website,
        }


@view_config(route_name='profile_list', renderer='pyramid_mumble:templates/profile_list.jinja2')
def profile_list_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    profiles = request.dbsession.query(models.MumbleUser).filter_by(is_speaker=True).order_by("realname").all()

    return {'profile_list': profiles, 'project': project, 'website': website}


@view_config(route_name='profile', renderer='pyramid_mumble:templates/profile.jinja2')
def profile_view(request):
    uid = request.matchdict['uid']
    if not uid and request.is_authenticated:
        return HTTPSeeOther(location=request.route_path('profile', request.identity.id))
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    profile = request.dbsession.query(models.MumbleUser).filter_by(id=uid).first()
    if not profile:
        raise HTTPNotFound()
    country = pycountry.countries.lookup(profile.country)
    if not profile:
        raise HTTPNotFound()

    sessions = []
    tz_local = pytz.timezone("America/Mexico_City")
    if request.identity.timezone:
        tz = pytz.timezone(request.identity.timezone)
    else:
        tz = tz_local
    for activity in profile.activities:
        session = {
            'id': activity.session.id,
            'title': str(activity.session),
            'start_time': tz_local.localize(activity.session.start_time).astimezone(tz=tz),
            'end_time': tz_local.localize(activity.session.end_time).astimezone(tz=tz),
        }
        sessions.append(session)

    return {'profile': profile, 'sessions': sessions, 'country': country,'project': project, 'website': website}


db_err_msg = """\
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for descriptions and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.

After you fix the problem, please restart the Pyramid application to
try it again.
"""
