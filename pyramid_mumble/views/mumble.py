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


@view_config(route_name='mumble_home', renderer='pyramid_mumble:templates/mumble.jinja2')
def mumble_view(request):
    """Returns the client application."""
    meeting = request.dbsession.query(models.Meeting).first()
    if meeting:
        project = meeting.title
    else:
        project = "A Pyramid Mumble Site"

140595906398192


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