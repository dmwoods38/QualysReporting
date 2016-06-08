from qgreports.scripts import get_scan_schedule
import qgreports.config.settings
import os
__author__ = 'dmwoods38'

username = qgreports.config.settings.QualysAPI.get('username', None)
password = qgreports.config.settings.QualysAPI.get('password', None)
outfile = os.path.join(qgreports.config.settings.report_folder,
                       'scan_schedule.csv')


def main():
    get_scan_schedule.main(outfile=outfile, username=username,
                           password=password)

if __name__ == '__main__':
    main()
