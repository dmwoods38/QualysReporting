import sys
import smtplib
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders

import os

import qgreports.qualys_connector as qc
import qgreports.config.settings

__author__ = "dmwoods38"

# TODO: This whole thing needs to be fixed to pull configurations
#       from the db.

user = qgreports.config.settings.QualysAPI['username']
password = qgreports.config.settings.QualysAPI['password']
report_folder = qgreports.config.settings.report_folder
archive_folder = qgreports.config.settings.archive_folder
email_from = qgreports.config.settings.email_from
smtp_server = qgreports.config.settings.smtp_server
# TODO: This needs to be fixed to pull from the db.
email_to = qgreports.config.settings.email_to


def build_email(file, subject):
    filename = file.rsplit('/')[-1]

    msg = MIMEMultipart()
    msg["From"] = email_from
    msg["To"] = email_to
    msg["Subject"] = subject

    fp = open(file, "rb")
    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(fp.read())
    fp.close()
    encoders.encode_base64(attachment)
    attachment.add_header("Content-Disposition", "attachment",
                          filename=filename)
    msg.attach(attachment)
    return msg


def send_jira_emails():
    server = smtplib.SMTP(smtp_server)

    for report in os.listdir(report_folder):
        base = report.rsplit('.')[0]
        msg = build_email(report_folder + report, base)
        server.sendmail(email_from, email_to, msg.as_string())

    server.quit()


def main():
    scans_with_files = {}
    if len(user) == 0 or len(password) == 0:
        print "Make sure you edit the file to include the user and pass"
        sys.exit(2)
    if len(sys.argv) < 2:
        print "Please enter a file with the scan names"
        sys.exit(2)
    else:
        try:
            with open(sys.argv[1], 'r') as f:
                for line in f:
                    k, v = tuple(line.strip('\n').split(','))
                    scans_with_files.update({k: v})
        except Exception as e:
            print "Error reading scan names"
            print e
            sys.exit(2)
    if len(scans_with_files):
        session = qc.login(user, password)
        try:
            scans_with_refs = qc.get_scan_refs(scans_with_files.keys(), session)
            refs_with_ids = qc.launch_scan_reports(scans_with_refs, session)
            # wait for scans to complete save API calls..
            time.sleep(120)
            report_status = qc.check_report_status(refs_with_ids, session)
            print report_status
            qc.get_reports(report_status['Finished'],
                           scans_with_refs['processed'],
                           scans_with_files, session)
            # if there are unfinished reports then continue to wait/check
            while len(''.join(report_status['Unfinished'].values())):
                print "Waiting for unfinished reports..."
                time.sleep(240)
                report_status = qc.check_report_status(
                    report_status['Unfinished'], session)
                qc.get_reports(report_status['Finished'],
                               scans_with_refs['processed'],
                               scans_with_files, session)
            print "Trying to send emails..."
            send_jira_emails()
        except Exception as e:
            print e
            sys.exit(2)
        finally:
            qc.logout(session)
    else:
        print "No scan names were found in" + str(sys.argv[1])
        sys.exit(2)

if __name__ == "__main__":
    main()
