import getpass
import qgreports.qualys_connector as qc
import qgreports.objects
from sys import exit
import traceback
__author__ = 'dmwoods38'


def main():
    user = raw_input('Qualys username: ')
    pw = getpass.getpass()
    scan_name = raw_input('Qualys Scan Name: ')
    qg_scan = qgreports.objects.Scan(scan_name=scan_name)
    session = qc.login(user, pw)

    try:
        qc.get_scan_refs([qg_scan], session)
        if not qg_scan.is_processed():
            print 'Scan is not currently processed'
            exit(0)

        merchant_user = raw_input('Qualys merchant username: ')
        params = {'action': 'share', 'scan_ref': qg_scan.scan_id,
                  'merchant_username': merchant_user}
        dest_url = '/api/2.0/fo/scan/pci/'
        response = qc.request(params, session, dest_url)
        if not qc.check_status(response):
            print 'Failed to share scan ' + qg_scan.scan_name
            print 'Scan ref: ' + qg_scan.scan_id
            exit(2)
        print 'Scan ' + qg_scan.scan_id + ' shared with merchant account'
    except Exception:
        traceback.print_exc()
        exit(2)
    finally:
        qc.logout(session)


if __name__ == '__main__':
    main()
