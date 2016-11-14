import sys
import smtplib
import time
import os
import qgreports.qualys_connector as qc
import qgreports.config.settings
import datetime
import traceback
import json
import logging.config
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
# from qgreports.models import QGReport, QGEmail, QGScan
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
report_config = os.path.dirname(qgreports.config.__file__) + '/reports.json'

logging.config.fileConfig(os.path.join(os.path.dirname(qgreports.config.__file__),
                          'logging_config.ini'))  
logger = logging.getLogger()

if 'add_timestamp' in qgreports.config.settings.__dict__:
    add_timestamp = qgreports.config.settings.add_timestamp
else:
    add_timestamp = True


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
    logger.info('Sending emails...')

    for report in reports:
        if report.report_filename is not None:
            msg = build_email(report.report_filename.replace("\\", ""),
                              report.email.subject, report.email.recipients)
            server.sendmail(email_from, msg.get_all('To'), msg.as_string())
            os.rename(report.report_filename, archive_folder +
                                     report.report_filename.rsplit('/')[-1])
            report.report_filename = archive_folder + \
                                     report.report_filename.rsplit('/')[-1]
    server.quit()


def main():
    # Get today's reports
    with open(report_config) as f:
        report_entries = json.load(f)
    scheduled_reports = []
    for report in report_entries:
        if report.get('day_of_month') == str(datetime.date.today().day):
            scheduled_reports.append(report)
        elif report.get('day_of_week') == str(datetime.date.today().weekday()):
            scheduled_reports.append(report)

    # if scheduled_reports.count() == 0:
    if len(scheduled_reports) == 0:
        logger.info('There were no scheduled reports today')
        sys.exit()
    report_list = []
    for report in scheduled_reports:
        email = Email(recipients=report.get('email_list'),
                      subject=report.get('email_subject'))
        scan = Scan(scan_name=report.get('scan_title'), is_map=report.get('is_map'))
        if report.get('output_csv') == 'True':
            r = Report(email=email, scan=scan, output='csv',
                       asset_groups=report.get('asset_groups'),
                       tags=report.get('tags'), asset_ips=report.get('asset_ips'),
                       template_id=report.get('template_id'))
            report_list.append(r)
        if report.get('output_pdf') == 'True':
            r = Report(email=email, scan=scan, output='pdf',
                       asset_groups=report.get('asset_groups'),
                       tags=report.get('tags'), asset_ips=report.get('asset_ips'),
                       template_id=report.get('template_id'))
            report_list.append(r)

    session = qc.login(user, password)
    try:
        # Handle scan reports
        scans = [x for x in report_list if not x.scan.is_map()]
        qc.get_scan_refs([x.scan for x in scans], session)
        qc.get_asset_group_ips(scans, session)

        # Handle map reports
        qc.get_map_refs([x.scan for x in report_list if x.scan.is_map()])
        qc.launch_scan_reports(report_list, session)
        # wait for reports to complete save API calls..
        wait = 120
        logger.info('Waiting %s seconds for reports to complete...' % wait)
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
            logger.info('Waiting for unfinished reports...')
            time.sleep(180)
            logger.info('Checking report status again...')
            qc.check_report_status(unfinished_reports, session)
            for report in unfinished_reports:
                if report.report_status.lower() == 'finished':
                    unfinished_reports.remove(report)

        qc.get_reports(report_list, session, add_timestamp)

        for report in report_list:
            if report.report_id is None:
                report_list.remove(report)
        # TODO:  Extract the destinations into some AbstractClass to allow
        #        easier extension.
        if destination == "email":
            send_emails(report_list)
        elif destination == "local":
            logger.info('Reports saved locally in: ' + report_folder)
        elif destination == "elasticsearch":
            import qgreports.elasticsearch_connector as es_connector
            logger.info('Putting scan results into elasticsearch')
            # Initialize elasticsearch mappings
            es = es_connector.initialize_es()
            for report in report_list:
                sanitized_report_name = report.report_filename.replace('\\', '')
                es_connector.es_scan_results(sanitized_report_name,
                                             report_tags=report.tags, es=es)
    except Exception as e:
        traceback.print_exc()
        sys.exit(2)
    finally:
        # Quick crappy way to get the API usage
        response = qc.request(params={'action': 'list'}, session=session,
                              dest_url='/api/2.0/fo/scan')
        qc.logout(session)
        logger.info('Number of API Requests remaining: %s' %
                    response.headers.get('X-RateLimit-Remaining'))


if __name__ == "__main__":
    main()
