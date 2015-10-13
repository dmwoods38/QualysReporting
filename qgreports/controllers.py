import qgreports.models
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

    def add_report(self, asset_groups, scan_id, email_id, day_of_month,
                   email_subject, report_run=None, output_pdf=None,
                   output_csv=None, active=True):
        entry = qgreports.models.QGReport(asset_groups=asset_groups,
                                          scan_id=scan_id, email_id=email_id,
                                          email_subject=email_subject,
                                          report_run=report_run,
                                          day_of_month=day_of_month,
                                          output_pdf=output_pdf,
                                          output_csv=output_csv, active=active)
        self.db_session.add(entry)

    # TODO: Update the next report run based on scan run time, report failure,
    # etc.

