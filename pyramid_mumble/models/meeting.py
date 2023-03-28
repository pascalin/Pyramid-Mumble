import sqlalchemy
from sqlalchemy.orm import relationship
import pytz, datetime

from .meta import Base


class Meeting(Base):
    __tablename__ = 'meetings'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text, default="")
    website = sqlalchemy.Column(sqlalchemy.Text, default="")
    start_time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    end_time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    timezone = sqlalchemy.Column(sqlalchemy.Text)
    tracks = relationship("Track")

    @property
    def ongoing(self):
        utc = pytz.UTC
        now = datetime.datetime.now(utc)
        return utc.localize(self.start_time) <= now <= utc.localize(self.end_time)


class Track(Base):
    __tablename__ = 'tracks'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text)
    description = sqlalchemy.Column(sqlalchemy.Text, default="")
    meeting_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('meetings.id'))
    sessions = relationship("Session", back_populates="track")

    def __str__(self):
        return self.title


class Session(Base):
    __tablename__ = 'sessions'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text, default="")
    description = sqlalchemy.Column(sqlalchemy.Text, default="")
    start_time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    end_time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    track_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('tracks.id'), default=None)
    track = relationship("Track", back_populates="sessions")
    activities = relationship("Activity", back_populates="session")

    def __str__(self):
        if self.title:
            return self.title
        else:
            return self.track.title


association_table = sqlalchemy.Table(
    "users_activities",
    Base.metadata,
    sqlalchemy.Column("activity_id", sqlalchemy.ForeignKey("activities.id"), primary_key=True),
    sqlalchemy.Column("performer_id", sqlalchemy.ForeignKey("models.id"), primary_key=True),
)


class Activity(Base):
    __tablename__ = 'activities'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    title = sqlalchemy.Column(sqlalchemy.Text, default="")
    description = sqlalchemy.Column(sqlalchemy.Text, default="")
    session_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('sessions.id'))
    session = relationship("Session", back_populates="activities")
    performers = relationship("MumbleUser", secondary=association_table, back_populates="activities")
