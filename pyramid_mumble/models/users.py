import sqlalchemy
from sqlalchemy.orm import relationship

from .meta import Base
from .meeting import association_table


class MumbleUser(Base):
    __tablename__ = 'models'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    username = sqlalchemy.Column(sqlalchemy.VARCHAR(100), unique=True, default=None)
    realname = sqlalchemy.Column(sqlalchemy.Text)
    organization = sqlalchemy.Column(sqlalchemy.Text, default="")
    country = sqlalchemy.Column(sqlalchemy.Text)
    state = sqlalchemy.Column(sqlalchemy.Text, default="")
    language = sqlalchemy.Column(sqlalchemy.Text)
    email = sqlalchemy.Column(sqlalchemy.VARCHAR(255), unique=True)
    password = sqlalchemy.Column(sqlalchemy.Text, default="")
    privkey = sqlalchemy.Column(sqlalchemy.Text, default=None)
    certificate = sqlalchemy.Column(sqlalchemy.Text, default=None)
    is_speaker = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_staff = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    lastlogin = sqlalchemy.Column(sqlalchemy.DateTime)
    timezone = sqlalchemy.Column(sqlalchemy.Text, default="")
    activities = relationship("Activity", secondary=association_table, back_populates="performers")


sqlalchemy.Index('my_index', MumbleUser.username, unique=True, mysql_length=255)
sqlalchemy.Index('my_index', MumbleUser.email, unique=True, mysql_length=255)
