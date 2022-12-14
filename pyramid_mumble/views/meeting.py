import deform.widget
from pyramid.csrf import new_csrf_token
from pyramid.httpexceptions import HTTPSeeOther, HTTPNotFound
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
from ..forms import meeting as meeting_forms

import datetime
import pytz
import itertools
import unidecode


@view_config(route_name='edit_meeting', renderer='pyramid_mumble:templates/admin_meeting.jinja2', permission='admin')
def meeting_edit(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        raise HTTPNotFound()

    appstruct = {
        'id': meeting.id,
        'title': meeting.title,
        'description': meeting.description,
        'website': meeting.website,
        'start_time': meeting.start_time,
        'end_time': meeting.end_time,
        'timezone': meeting.timezone,
        'tracks': [{'id': track.id, 'title':track.title, 'description':track.description} for track in meeting.tracks],
    }

    meeting_schema = meeting_forms.MeetingSchema().bind(timezone_default=meeting.timezone)
    form = Form(meeting_schema, buttons=[Button('submit',)])

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'meeting_form': e.render(), 'meeting': meeting, 'project': project, 'website': website, 'appstruct': appstruct}

        if meeting.title != appstruct['title']:
            meeting.title = appstruct['title']
        if meeting.website != appstruct['website']:
            meeting.website = appstruct['website']
        if meeting.timezone != appstruct['timezone']:
            meeting.timezone = appstruct['timezone']
        if meeting.description != appstruct['description']:
            meeting.description = appstruct['description']
        if meeting.start_time != appstruct['start_time']:
            meeting.start_time = appstruct['start_time']
        if meeting.end_time != appstruct['end_time']:
            meeting.end_time = appstruct['end_time']
        for track in appstruct['tracks']:
            if not track['id']:
                new_track = models.Track(title=track['title'], description=track['description'], meeting_id=meeting.id)
                request.dbsession.add(new_track)
            else:
                extant_track = request.dbsession.query(models.Track).filter_by(id=track['id'], meeting_id=meeting.id).one()
                if extant_track.title != track['title']:
                    extant_track.title = track['title']
                if extant_track.description != track['description']:
                    extant_track.description = track['description']

        return HTTPSeeOther(request.route_path("home"))

    return {'meeting_form': form.render(appstruct=appstruct), 'meeting': meeting, 'project': project, 'website': website}


@view_config(route_name='schedule', renderer='pyramid_mumble:templates/schedule.jinja2')
def schedule_view(request):
    detailed = False
    if 'detailed' in request.GET:
        detailed = True
    year = request.matchdict.get('year')
    month = request.matchdict.get('month')
    day = request.matchdict.get('day')
    meeting = request.dbsession.query(models.Meeting).first()
    tracks = request.dbsession.query(models.Track).filter_by(meeting_id=meeting.id)
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''
    sessions = []

    for track in tracks:
        # track_sessions = request.dbsession.query(models.Session).filter_by(track_id=track.id)
        sessions.extend(track.sessions)
    sessions.sort(key=lambda s:s.start_time)

    return {'tracks': tracks, 'sessions': sessions, 'project': project, 'website': website, 'schedule_date': "", 'detailed': detailed}



@view_config(route_name='session', renderer='pyramid_mumble:templates/session.jinja2')
def session_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    session_id = request.matchdict.get('session_id')
    session = request.dbsession.query(models.Session).filter_by(id=session_id).first()
    if not session:
        raise HTTPNotFound()

    tz_local = pytz.timezone("America/Mexico_City")
    if request.identity.timezone:
        tz = pytz.timezone(request.identity.timezone)
    else:
        tz = tz_local
    s = {
        'title': str(session),
        'track': session.track,
        'start_time': tz_local.localize(session.start_time).astimezone(tz=tz),
        'end_time': tz_local.localize(session.end_time).astimezone(tz=tz),
        'description': session.description,
        'activities': session.activities,
    }


    return {'session': s, 'project': project, 'website': website}


@view_config(route_name='edit_session', renderer='pyramid_mumble:templates/admin_sessions.jinja2', permission='admin')
def session_edit_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    session_id = request.matchdict.get('session_id')
    session = request.dbsession.query(models.Session).filter_by(id=session_id).first()
    if not session:
        raise HTTPNotFound()

    appstruct = {
        'id': session.id,
        'title': session.title,
        'description': session.description,
        'start_time': session.start_time,
        'end_time': session.end_time,
        'track': session.track_id,
        'activities': [{'id': activity.id, 'title':activity.title, 'description':activity.description} for activity in session.activities],
    }

    session_schema = admin.SessionSchema().bind(tracks=meeting.tracks, default_track=session.track)
    form = Form(session_schema, buttons=[Button('submit',)])

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'session_form': e.render(), 'session': session, 'project': project, 'website': website, 'appstruct': appstruct}

        if session.title != appstruct['title']:
            session.title = appstruct['title']
        if session.description != appstruct['description']:
            session.description = appstruct['description']
        if session.start_time != appstruct['start_time']:
            session.start_time = appstruct['start_time']
        if session.end_time != appstruct['end_time']:
            session.end_time = appstruct['end_time']
        if session.track_id != appstruct['track']:
            session.track_id = appstruct['track']
        for activity in appstruct['activities']:
            if not activity['id']:
                new_activity = models.Activity(title=activity['title'], description=activity['description'], session_id=session.id)
                request.dbsession.add(new_activity)
            else:
                extant_activity = request.dbsession.query(models.Activity).filter_by(id=activity['id'], session_id=session.id).first()
                if extant_activity.title != activity['title']:
                    extant_activity.title = activity['title']
                if extant_activity.description != activity['description']:
                    extant_activity.description = activity['description']

        return HTTPSeeOther(request.route_path("session", session_id=session.id))

    return {'session_form': form.render(appstruct=appstruct), 'session': session, 'project': project, 'website': website}


@view_config(route_name='activity', renderer='pyramid_mumble:templates/activity.jinja2')
def activity_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''

    activity_id = request.matchdict.get('activity_id')
    activity = request.dbsession.query(models.Activity).filter_by(id=activity_id).first()
    if not activity:
        raise HTTPNotFound()

    return {'activity': activity, 'project': project, 'website': website}


@view_config(route_name='edit_activity', renderer='pyramid_mumble:templates/admin_activities.jinja2', permission='admin')
def activity_edit_view(request):
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"

    activity_id = request.matchdict.get('activity_id')
    activity = request.dbsession.query(models.Activity).filter_by(id=activity_id).first()
    if not activity:
        raise HTTPNotFound()

    sessions = request.dbsession.query(models.Session).all()
    speakers = request.dbsession.query(models.MumbleUser).filter_by(is_speaker=True)
    current_performer_ids = {performer.id for performer in activity.performers}

    appstruct = {
        'id': activity.id,
        'description': activity.description,
        'title': activity.title,
        'session': activity.session_id,
        'performers': current_performer_ids,
    }

    activity_schema = admin.ActivitySchema().bind(sessions=sessions, performers=speakers)
    form = Form(activity_schema, buttons=[Button('submit',)])

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            appstruct = form.validate(controls)
        except ValidationFailure as e:
            return {'activity_form': e.render(), 'activity': activity, 'project': project, 'website': website,}

        if activity.title != appstruct['title']:
            activity.title = appstruct['title']
        if activity.description != appstruct['description']:
            activity.description = appstruct['description']
        if activity.session_id != appstruct['session']:
            activity.session_id = appstruct['session']

        existing = current_performer_ids & appstruct['performers']
        for p_id in appstruct['performers'] - existing:
            performer = speakers.filter_by(id=p_id).one()
            activity.performers.append(performer)
        for p_id in current_performer_ids - existing:
            performer = speakers.filter_by(id=p_id).one()
            activity.performers.remove(performer)

        return HTTPSeeOther(request.route_path("session", session_id=activity.session_id))

    return {'activity_form': form.render(appstruct=appstruct), 'activity': activity, 'project': project, 'website': website}
