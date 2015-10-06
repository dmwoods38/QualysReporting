__author__ = 'dmwoods38'

debug = False

DATABASE = {
    "comment": "Works for DBs that are supported by SQLAlchemy.",
    "db_type": "postgresql",
    "db_name": "qualysguard",
    "db_user": "postgres",
    "db_pass": "qgpostgres",
    "db_server": "localhost"
}

# scan_template - template id for a scan report template that has similar
#                 settings to the Quick Actions report.
QualysAPI = {
    "username": "",
    "password": "",
    "url": "https://qualysapi.qualys.com",
    "scan_template": ""
}

# where reports are temporarily stored before being emailed.
report_folder = ""

# sender
email_from = ''

# email server used to send the reports.
smtp_server = ''