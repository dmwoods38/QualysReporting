import sys
import smtplib
import time
import os
import qgreports.qualys_connector as qc
import qgreports.config.settings
import qgreports.models
import datetime
from sqlalchemy.orm import sessionmaker
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from qgreports.models import QGReport, QGEmail, QGScan
from qgreports.objects import Scan, Email, Report

__author__ = "dmwoods38"

# TODO: This whole thing needs to be fixed to pull configurations
#       from the db.

user = qgreports.config.settings.QualysAPI['username']
password = qgreports.config.settings.QualysAPI['password']
report_folder = qgreports.config.settings.report_folder
archive_folder = qgreports.config.settings.archive_folder
email_from = qgreports.config.settings.email_from
smtp_server = qgreports.config.settings.smtp_server
# TODO: Grab email_to from db.
email_to = qgreports.config.settings.email_to
debug = qgreports.config.settings.debug


def build_email(report, subject):
    filename = report.rpartition('/')[-1]

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
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


def send_emails():
    server = smtplib.SMTP(smtp_server)

    print "Email_to: " + email_to
    # TODO: Change to take in report objects
    for report in os.listdir(report_folder):
        base = report.rpartition('.')[0]
        msg = build_email(report_folder + report, email_pre + base +
                          report.rpartition('.')[-1].upper())
        server.sendmail(email_from, msg.get_all('To'), msg.as_string())

    os.system("mv " + report_folder + "* " + archive_folder)
    server.quit()


def print_usage():
    print "Usage: "
    print "      python get_reports.py"


# TODO: Fix to pull everything from DB.
def main():
    # Set up DB connection
    engine = qgreports.models.db_init()
    Session = sessionmaker(bind=engine)
    db_session = Session()

    # scans_with_files = {}
    if len(sys.argv) != 1:
        print_usage()
        sys.exit(2)

    # Get today's reports
    scheduled_reports = db_session.query(QGEmail,
                                      QGScan,
                                      QGReport).join(QGReport).join(QGScan)
    scheduled_reports = scheduled_reports.filter(QGReport.day_of_month ==
                                                 datetime.date.today().day)
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
                            asset_groups=report_result.asset_groups)
            report_list.append(report)
        if report_result.output_pdf:
            report = Report(email=email, scan=scan, output='pdf',
                            asset_groups=report_result.asset_groups)
            report_list.append(report)

    # else:
        # try:
        #     # TODO: Get the scans and file names from DB
        #     with open(sys.argv[1], 'r') as f:
        #         for line in f:
        #             k, v = tuple(line.strip('\n').split(','))
        #             scans_with_files.update({k: v})
        #     # TODO: Get the emails from the DB
        #     with open(sys.argv[2], 'r') as f:
        #         global email_to
        #         email_to = f.read().strip()
        #         print "Email_to from file: " + email_to
        # except Exception as e:
        #     print "Error reading scan names"
        #     print e
        #     sys.exit(2)
    session = qc.login(user, password)
    try:
        qc.get_scan_refs([x.scan for x in report_list], session)
        qc.launch_scan_reports(report_list, session)

        # wait for reports to complete save API calls..
        time.sleep(120)
        qc.check_report_status(report_list, session)
        finished_reports = []
        unfinished_reports = []
        for report in report_list:
            if report.report_status.lower() == 'finished':
                finished_reports.append(report)
            else:
                unfinished_reports.append(report)

        # TODO: Change get_reports method
    except Exception as e:
        print e
        sys.exit(2)
    finally:
        qc.logout(session)
    # if len(scans_with_files):
    #     session = qc.login(user, password)
    #     try:
    #         scans_with_refs = qc.get_scan_refs(scans_with_files.keys(), session)
    #
    #         refs_with_ids = qc.launch_scan_reports(scans_with_refs, session, formats=['pdf'])
    #         # wait for scans to complete save API calls..
    #         time.sleep(120)
    #         report_status = qc.check_report_status(refs_with_ids, session)
    #         print report_status
    #         if len(''.join(status for statuses in report_status['Finished'].values()
    #                             for status in statuses)):
    #             qc.get_reports(report_status['Finished'], scans_with_refs['processed'], scans_with_files, session)
    #         # if there are unfinished reports then continue to wait/check
    #         while(len(''.join(status for statuses in report_status['Unfinished'].values()
    #                                 for status in statuses))):
    #             print "Waiting for unfinished reports..."
    #             time.sleep(240)
    #             print "Checking report status again..."
    #             if debug:
    #                 print report_status['Unfinished']
    #             report_status = qc.check_report_status(report_status['Unfinished'], session)
    #             if debug:
    #                 print "report_status : " + report_status.__str__()
    #             if len(''.join(status for statuses in report_status['Finished'].values()
    #                                 for status in statuses)):
    #                 qc.get_reports(report_status['Finished'],
    #                                scans_with_refs['processed'],
    #                                scans_with_files, session)
    #         print "Trying to send emails..."
    #         send_emails()
    #     except Exception as e:
    #         print e
    #         sys.exit(2)
    #     finally:
    #         qc.logout(session)
    # else:
    #     print "No scan names were found in" + str(sys.argv[1])
    #     sys.exit(2)

    # Close out the db
    db_session.close()
    engine.dispose()
if __name__ == "__main__":
    main()
