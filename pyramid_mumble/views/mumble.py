import logging

from pyramid.httpexceptions import HTTPSeeOther
from pyramid.view import (
    view_config,
)
from .. import models

import os
import uuid
import wave

# from flask import Blueprint, current_app, session, url_for, render_template
# from flask_socketio import emit
# from socketio_examples import socketio

# bp = Blueprint('audio', __name__, static_folder='static',
#                template_folder='templates')

@view_config(route_name='mumble_join', renderer='pyramid_mumble:templates/mumble.jinja2')
def mumble_view(request):
    """Returns the client application."""
    channel = request.matchdict['channel']
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
        website = meeting.website
    else:
        project = "A Pyramid Mumble Site"
        website = ''
    mumble = request.context.mumble
    if not mumble.is_alive():
        mumble.start()
        mumble.is_ready()
        channel = mumble.my_channel()
        mumble_user = mumble.users.myself
        mumble_user.mute()

        sio = request.sio

        @sio.on('*')
        def catch_all(event, sid, data):
            logging.WARN(f"Event '{event}' received from {sid} client.'")

        @sio.on('start-recording', namespace='/audio')
        def start_recording(sid, options):
            # """Start recording audio from the client."""
            # id = uuid.uuid4().hex  # server-side filename
            # session['wavename'] = id + '.wav'
            # wf = wave.open(current_app.config['FILEDIR'] + session['wavename'], 'wb')
            # wf.setnchannels(options.get('numChannels', 1))
            # wf.setsampwidth(options.get('bps', 16) // 8)
            # wf.setframerate(options.get('fps', 44100))
            # session['wavefile'] = wf
            mumble.users.myself.unmute()

        @sio.on('write-audio', namespace='/audio')
        def write_audio(sid,data):
            """Write a chunk of audio from the client."""
            mumble.sound_output.add_sound(data)

        @sio.on('end-recording', namespace='/audio')
        def end_recording(sid):
            """Stop recording audio from the client."""
            mumble.users.myself.mute()

    elif channel and mumble.my_channel['name'] != channel[0]:
        new_channel = mumble.channels.find_by_name(channel)

    mumble_user = mumble.users.myself

    return {'project': project, 'website': website, 'mumble_channel': channel, 'mumble_user': mumble_user,}


@view_config(route_name='mumble_leave')
def mumble_leave(request):
    mumble_factory = request.context
    mumble_factory.mumble.stop()
    del mumble_factory.connections[request.identity.email]

    return HTTPSeeOther(request.route_path("home"))

# @socketio.on('start-recording', namespace='/audio')
# def start_recording(options):
#     """Start recording audio from the client."""
#     id = uuid.uuid4().hex  # server-side filename
#     session['wavename'] = id + '.wav'
#     wf = wave.open(current_app.config['FILEDIR'] + session['wavename'], 'wb')
#     wf.setnchannels(options.get('numChannels', 1))
#     wf.setsampwidth(options.get('bps', 16) // 8)
#     wf.setframerate(options.get('fps', 44100))
#     session['wavefile'] = wf
#
#
# @socketio.on('write-audio', namespace='/audio')
# def write_audio(data):
#     """Write a chunk of audio from the client."""
#     session['wavefile'].writeframes(data)
#
#
# @socketio.on('end-recording', namespace='/audio')
# def end_recording():
#     """Stop recording audio from the client."""
#     emit('add-wavefile', url_for('static',
#                                  filename='_files/' + session['wavename']))
#     session['wavefile'].close()
#     del session['wavefile']
#     del session['wavename']