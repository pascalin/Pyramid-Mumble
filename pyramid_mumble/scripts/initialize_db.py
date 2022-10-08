import argparse
import sys
import datetime
import pytz

from pyramid.paster import bootstrap, setup_logging
from sqlalchemy.exc import OperationalError

from .. import models


def setup_models(dbsession):
    """
    Add or update models / fixtures in the database.

    """
    model = models.users.MumbleUser(
        realname='Mumble Admin User',
        username="Mumble_Admin",
        organization="Apuntia Networks",
        country="MX",
        state="CdMx",
        email="mumble@hapuntia.com",
        language="English",
        is_staff=True,
        timezone="America/Mexico_City",
    )
    dbsession.add(model)

    tz_mexico = pytz.timezone('America/Mexico_City')
    start_time = datetime.datetime(2022, 10, 3, 9, 0, 0, 0, tzinfo=tz_mexico)
    end_time = datetime.datetime(2022, 10, 7, 14, 0, 0, 0, tzinfo=tz_mexico)

    meeting = models.Meeting(title="A Pyramid Mumble Meeting",
                            start_time=start_time, end_time=end_time, timezone='America/Mexico_City')
    dbsession.add(meeting)

    topics = ["Pyramid", "Mumble", "Pyramid-Mumble"]
    tracks = []
    for topic in topics:
        _ = models.Track(title=topic, meeting_id=1)
        tracks.append(_)
        dbsession.add(_)

    time = start_time
    session_duration = datetime.timedelta(hours=1)
    next_day = datetime.timedelta(hours=19)
    while time < end_time:
        session = models.Session(start_time=time, end_time=time+session_duration, track_id=1)
        dbsession.add(session)
        time += session_duration
        if time.hour >= 14:
            time += next_day

def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config_uri',
        help='Configuration file, e.g., development.ini',
    )
    return parser.parse_args(argv[1:])


def main(argv=sys.argv):
    args = parse_args(argv)
    setup_logging(args.config_uri)
    env = bootstrap(args.config_uri)

    try:
        with env['request'].tm:
            dbsession = env['request'].dbsession
            setup_models(dbsession)
    except OperationalError:
        print('''
Pyramid is having a problem using your SQL database.  The problem
might be caused by one of the following things:

1.  You may need to initialize your database tables with `alembic`.
    Check your README.txt for description and try to run it.

2.  Your database server may not be running.  Check that the
    database server referred to by the "sqlalchemy.url" setting in
    your "development.ini" file is running.
            ''')
