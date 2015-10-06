from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Sequence
import settings
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
__author__ = 'dmwoods38'

Base = declarative_base()


class QGScan(Base):
    __tablename__ = 'qgscans'
    id = Column(Integer, Sequence('qgscans_seq_id'), primary_key=True)
    scan_title = Column(String, nullable=False)
    next_run = Column(DateTime)


class QGEmail(Base):
    __tablename__ = 'qgemails'
    id = Column(Integer, Sequence('qgemails_seq_id'), primary_key=True)
    email_list = Column(String, nullable=False)


class QGReport(Base):
    __tablename__ = 'qgreports'
    id = Column(Integer, Sequence('qgreports_seq_id'), primary_key=True)
    asset_groups = Column(String)
    scan_id = Column(Integer, ForeignKey('qgscans.id'), nullable=False)
    email_id = Column(Integer, ForeignKey('qgemails.id'), nullable=False)
    report_title = Column(String)
    next_report_run = Column(DateTime)
    output_pdf = Column(Boolean)
    output_csv = Column(Boolean)
    active = Column(Boolean)


def db_init():
    engine = create_engine(URL(**settings.DATABASE))
    Base.metadata.create_all(engine)