import qgreports.controllers
import qgreports.models
from qgreports.models import QGScan, QGEmail, QGReport
from sqlalchemy.orm import sessionmaker
import os
import json

# Script to add large amount of reports to the db from a JSON file.
# This will also fill in all the other necessary tables.
__author__ = 'dmwoods38'

reports_path = os.path.dirname(os.path.realpath(__file__))
reports_path += '/../config/reports.json'


def main():
    engine = qgreports.models.db_init()
    Session = sessionmaker(bind=engine)
    session = Session()
    distribution_lists = {}
    scans_list = set()

    with open(reports_path) as reports_file:
        reports = json.load(reports_file)

    # Populate emails and scans
    for report in reports:
        dl_name = report['list_name'].encode('utf8', 'ignore')
        dl_emails = report['email_list'].encode('utf8', 'ignore')
        distribution_lists.update({dl_name: dl_emails})
        scan_title = report['scan_title'].encode('utf8', 'ignore')
        scans_list.add(scan_title)

    email_entries = set()
    for list_name, email_list in distribution_lists.iteritems():
        email_entries.add(QGEmail(email_list=email_list,
                                     list_name=list_name))
    session.add_all(email_entries)
    session.commit()

    scan_entries = set()
    for scan in scans_list:
        scan_entries.add(QGScan(scan_title=scan))

    session.add_all(scan_entries)
    session.commit()

    qgemails = session.query(QGEmail)
    qgscans = session.query(QGScan)
    for report in reports:
        asset_groups = report['asset_groups'].encode('utf8', 'ignore')
        scan_title = report['scan_title'].encode('utf8', 'ignore')
        if 'day_of_month' in report:
            day_of_month = int(report['day_of_month'])
        else:
            day_of_month = None
        if 'day_of_week' in report:
            day_of_week = int(report['day_of_week'])
        else:
            day_of_week = None
        if 'tags' in report:
            tags = ','.join(report['tags']).encode('utf8', 'ignore')
        else:
            tags = None
        result = qgscans.filter(QGScan.scan_title == scan_title)[:1]
        scan_id = result[0].id
        list_name = report['list_name'].encode('utf8', 'ignore')
        result = qgemails.filter(QGEmail.list_name == list_name)[:1]
        email_id = result[0].id
        email_subject = report['email_subject'].encode('utf8', 'ignore')
        output_pdf = report['output_pdf'].encode('utf8', 'ignore').lower() == \
                     'true'
        output_csv = report['output_csv'].encode('utf8', 'ignore').lower() == \
                     'true'
        session.add(QGReport(asset_groups=asset_groups, scan_id=scan_id,
                             email_id=email_id, output_pdf=output_pdf,
                             output_csv=output_csv, day_of_month=day_of_month,
                             day_of_week=day_of_week,
                             email_subject=email_subject, tags=tags))
    # At the very end commit the session.
    session.commit()

    # cleanup of connections.
    session.close()
    engine.dispose()


if __name__ == '__main__':
    main()
