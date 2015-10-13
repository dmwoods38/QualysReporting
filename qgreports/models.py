from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy import Sequence
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL

from qgreports.config import settings

__author__ = 'dmwoods38'

Base = declarative_base()


class QGScan(Base):
    __tablename__ = 'qgscans'
    id = Column(Integer, Sequence('qgscans_seq_id'), primary_key=True)
    scan_title = Column(String, nullable=False, unique=True)
    next_run = Column(DateTime)


class QGEmail(Base):
    __tablename__ = 'qgemails'
    id = Column(Integer, Sequence('qgemails_seq_id'), primary_key=True)
    list_name = Column(String, nullable=False, unique=True)
    email_list = Column(String, nullable=False)


class QGReport(Base):
    __tablename__ = 'qgreports'
    id = Column(Integer, Sequence('qgreports_seq_id'), primary_key=True)
    asset_groups = Column(String)
    scan_id = Column(Integer, ForeignKey('qgscans.id'), nullable=False)
    email_id = Column(Integer, ForeignKey('qgemails.id'), nullable=False)
    email_subject = Column(String, nullable=False)
    # This is not used right now, in here for future use.
    report_run = Column(DateTime)
    day_of_month = Column(Integer, nullable=False)
    output_pdf = Column(Boolean, nullable=False)
    output_csv = Column(Boolean, nullable=False)
    active = Column(Boolean, default=True)


def db_init():
    engine = create_engine(URL(**settings.DATABASE))
    Base.metadata.create_all(engine)
    return engine
