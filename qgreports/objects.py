__author__ = 'dmwoods38'


class Scan:
    def __init__(self, scan_id=None, scan_name=None, scan_state=None):
        self.scan_id = scan_id
        self.scan_name = scan_name
        self.scan_state = scan_state

    def is_processed(self):
        if self.scan_state.lower() == 'processed':
            return True


class Email:
    def __init__(self, subject=None, recipients=None):
        self.subject = subject
        self.recipients = recipients


class Report:
    def __init__(self, report_id=None, report_status=None,
                 email=None, scan=None, filename=None, output=None,
                 asset_groups=None, asset_ips=None):
        self.report_id = report_id
        self.report_status = report_status
        self.email = email
        self.scan = scan
        self.report_filename = filename
        self.output = output
        self.asset_groups = asset_groups
        self.asset_ips = asset_ips


class Vuln:
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)





