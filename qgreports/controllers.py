import qgreports.models
import sqlalchemy
__author__ = 'dmwoods38'


class QGEmailController:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_email_list(self, email_list, list_name):
        entry = qgreports.models.QGEmail(email_list=email_list,
                                         list_name=list_name)
        self.db_session.add(entry)


class QGScanController:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_scan(self, scan_title, next_run=None):
        entry = qgreports.models.QGScan(scan_title=scan_title,
                                        next_run=next_run)
        self.db_session.add(entry)

    # TODO: Update next scan run date using the API


class QGReportController:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_report(self, asset_groups, scan_id, email_id, email_subject,
                   day_of_month=None, day_of_week=None,
                   report_run=None, output_pdf=None, output_csv=None,
                   active=True):
        entry = qgreports.models.QGReport(asset_groups=asset_groups,
                                          scan_id=scan_id, email_id=email_id,
                                          email_subject=email_subject,
                                          report_run=report_run,
                                          day_of_month=day_of_month,
                                          day_of_week=day_of_week,
                                          output_pdf=output_pdf,
                                          output_csv=output_csv, active=active)
        self.db_session.add(entry)

    # TODO: Update the next report run based on scan run time, report failure,
    # etc.


class QGVulnController:
    def __init__(self, db_session):
        self.db_session = db_session

    def add_vuln(self, ip, qid, severity, scan_date, timezone,
                 pci_scope, scope, os=None, dns=None):
        entry = qgreports.models.QGVuln(dns=dns, qid=qid, severity=severity,
                                        scan_date=scan_date, timezone=timezone,
                                        pci_scope=pci_scope, scope=scope,
                                        ip=ip, os=os)

        self.db_session.add(entry)

    def add_all_vulns(self, vulns):
        entries = []
        ips = list({vuln.ip for vuln in vulns})
        self.db_session.query(qgreports.models.QGVuln).filter(
            qgreports.models.QGVuln.ip.in_(ips)).delete(
            synchronize_session='fetch')
        for vuln in vulns:
            entries.append(
                qgreports.models.QGVuln(dns=vuln.dns, qid=vuln.qid,
                                        severity=vuln.severity,
                                        scan_date=vuln.scan_date,
                                        timezone=vuln.timezone,
                                        pci_scope=vuln.pci_scope,
                                        scope=vuln.scope,
                                        ip=vuln.ip, os=vuln.os))

        self.db_session.add_all(entries)
