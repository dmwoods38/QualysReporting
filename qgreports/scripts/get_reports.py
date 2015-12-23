import sys
import smtplib
import time
import os
import qgreports.qualys_connector as qc
import qgreports.config.settings
import qgreports.models
import qgreports.controllers
import qgreports.elasticsearch_connector as es_connector
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import or_
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from qgreports.models import QGReport, QGEmail, QGScan
from qgreports.objects import Scan, Email, Report

__author__ = "dmwoods38"

user = qgreports.config.settings.QualysAPI['username']
password = qgreports.config.settings.QualysAPI['password']
report_folder = qgreports.config.settings.report_folder
archive_folder = qgreports.config.settings.archive_folder
email_from = qgreports.config.settings.email_from
smtp_server = qgreports.config.settings.smtp_server
debug = qgreports.config.settings.debug
destination = qgreports.config.settings.destination


def build_email(report, subject, recipients):
    filename = report.rpartition('/')[-1]

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = recipients
    msg["Subject"] = subject

    fp = open(report, "rb")
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment",
                          filename=filename)
    msg.attach(attachment)
    return msg


def send_emails(reports):
    server = smtplib.SMTP(smtp_server)
    print "Sending emails..."

    for report in reports:
        if report.report_filename is not None:
            msg = build_email(report.report_filename.replace("\\", ""),
                              report.email.subject, report.email.recipients)
            server.sendmail(email_from, msg.get_all('To'), msg.as_string())
            os.system("mv " + report.report_filename + " " + archive_folder)
            report.report_filename = archive_folder + \
                                     report.report_filename.rsplit('/')[-1]
    server.quit()


def main():
    # Set up DB connection
    engine = qgreports.models.db_init()
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # Get today's reports
    scheduled_reports = db_session.query(QGEmail,
                                      QGScan,
                                      QGReport).join(QGReport).join(QGScan)
    scheduled_reports = scheduled_reports.filter(
        or_(QGReport.day_of_month == datetime.date.today().day,
            QGReport.day_of_week == datetime.date.today().weekday()))
    if scheduled_reports.count() == 0:
        if debug:
            print "There were no scheduled reports on: " + \
                  datetime.date.today().__str__()
        db_session.close()
        engine.dispose()
        sys.exit()
    report_list = []
    # Parse the scheduled_reports into objects for easier manipulation.
    for row in scheduled_reports:
        report_result = row[2]
        email = Email(recipients=row[0].email_list,
                      subject=report_result.email_subject)
        scan = Scan(scan_name=row[1].scan_title)
        if report_result.output_csv:
            report = Report(email=email, scan=scan, output='csv',
                            asset_groups=report_result.asset_groups,
                            tags=report_result.tags)
            report_list.append(report)
        if report_result.output_pdf:
            report = Report(email=email, scan=scan, output='pdf',
                            asset_groups=report_result.asset_groups,
                            tags=report_result.tags)
            report_list.append(report)

    session = qc.login(user, password)
    try:
        qc.get_scan_refs([x.scan for x in report_list], session)
        qc.get_asset_group_ips(report_list, session)
        qc.launch_scan_reports(report_list, session)

        # wait for reports to complete save API calls..
        wait = 120
        print "Waiting " + str(wait) + " seconds for reports to complete..."
        time.sleep(wait)
        qc.check_report_status(report_list, session)
        unfinished_reports = []
        for report in report_list:
            if report.report_status is None:
                report_list.remove(report)
                continue
            if report.report_status.lower() != 'finished':
                unfinished_reports.append(report)

        while len(unfinished_reports):
            print "Waiting for unfinished reports..."
            time.sleep(180)
            print "Checking report status again..."
            qc.check_report_status(unfinished_reports, session)
            for report in unfinished_reports:
                if report.report_status.lower() == 'finished':
                    unfinished_reports.remove(report)

        qc.get_reports(report_list, session)

        for report in report_list:
            if report.report_id is None:
                report_list.remove(report)
        if destination == "email":
            send_emails(report_list)
        elif destination == "local":
            print "Reports saved locally in: " + report_folder
        elif destination == "elasticsearch":
            print "Putting scan results into elasticsearch"
            # Initialize elasticsearch mappings
            es = es_connector.initialize_es()
            for report in report_list:
                sanitized_report_name = report.report_filename.replace('\\',
                                                                       '')
                es_connector.es_scan_results(sanitized_report_name,
                                             report_tags=report.tags, es=es)
    except Exception as e:
        print e
        sys.exit(2)
    finally:
        qc.logout(session)

    # Close out the db
    db_session.close()
    engine.dispose()
if __name__ == "__main__":
    main()
