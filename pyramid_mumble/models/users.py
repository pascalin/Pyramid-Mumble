from sqlalchemy import (
    Column,
    Index,
    Integer,
    Text,
    Boolean,
    LargeBinary,
    DateTime,
    VARCHAR,
)
from sqlalchemy.orm import relationship

from .meta import Base
from .meeting import association_table


class MumbleUser(Base):
    __tablename__ = 'models'
    id = Column(Integer, primary_key=True)
    username = Column(VARCHAR(100), unique=True, default=None)
    realname = Column(Text)
    organization = Column(Text, default="")
    country = Column(Text)
    state = Column(Text, default="")
    language = Column(Text)
    email = Column(VARCHAR(255), unique=True)
    password = Column(Text, default="")
    publickey = Column(LargeBinary)
    is_speaker = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    lastlogin = Column(DateTime)
    timezone = Column(Text, default="")
    activities = relationship("Activity", secondary=association_table, back_populates="performers")


Index('my_index', MumbleUser.username, unique=True, mysql_length=255)
Index('my_index', MumbleUser.email, unique=True, mysql_length=255)
