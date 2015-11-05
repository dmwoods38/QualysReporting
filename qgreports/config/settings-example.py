__author__ = 'dmwoods38'

debug = False

DATABASE = {
    'db_type': 'postgresql',
    'db_name': 'qualysguard',
    'db_user': 'postgres',
    'db_pass': 'qgpostgres',
    'db_server': 'localhost'
}

# scan_template - template id for a scan report template that has similar
#                 settings to the Quick Actions report.
QualysAPI = {
    'username': '',
    'password': '',
    'url': 'https://qualysapi.qualys.com',
    'scan_template': ''
}

# where reports are temporarily stored before being emailed.
report_folder = ''

# report archive folder after reports are emailed.
archive_folder = ''

# log file for any unprocessed reports. sorry it looks terrible atm.
unprocessed_log = ''
# sender
email_from = ''

# email server used to send the reports.
smtp_server = ''

# Destination setting, should probably find a better way of doing this eventually.
# local - saving to report_folder only, no emailing
# email - use report_folder as temp storage, then send to
destination = 'local'