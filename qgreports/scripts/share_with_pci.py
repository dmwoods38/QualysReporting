import getpass
import qgreports.qualys_connector as qc
import qgreports.objects
import time
from xml.etree import ElementTree as ET
from sys import exit
import traceback
__author__ = 'dmwoods38'


def main(**kwargs):
    user = kwargs.get('user', None)
    if user is None:
        user = raw_input('Qualys username: ')
    password = kwargs.get('password', None)
    if password is None:
        password = getpass.getpass()
    scan_name = kwargs.get('scan_name', None)
    if scan_name is None:
        raw_input('Qualys Scan Name: ')

    qg_scan = qgreports.objects.Scan(scan_name=scan_name)
    session = qc.login(user, password)

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
        sleeptime = 720
        status_xml = ET.fromstring(response.text.encode('utf8', 'ignore'))
        if 'Finished' in status_xml.findtext('.//TEXT', []):
            print 'Scan ' + qg_scan.scan_id + \
                  ' shared with merchant account'
            return

        # Check share status
        for i in range(0, 3):
            status_response = qc.get_pci_share_status(session,
                                                      qg_scan.scan_id,
                                                      merchant_user)
            status_xml = ET.fromstring(status_response.text.encode(
                'utf8', 'ignore'
            ))
            if 'Finished' in status_xml.findtext('.//STATUS', []):
                print 'Scan ' + qg_scan.scan_id + \
                      ' shared with merchant account'
                return
            print 'Waiting %s seconds for report to be shared' % sleeptime
            time.sleep(720)
        exit(2)
        # Should check the response for failed shares, and then
        # get the pci share status. If it is finished then this can
        # exit cleanly because it doesn't need to be shared.
        # If it is in progress, just wait and recheck until the
        # scan is fully imported into the merchant account.
        # if not qc.check_status(response):
        #     print 'Failed to share scan ' + qg_scan.scan_name
        #     print 'Scan ref: ' + qg_scan.scan_id
        #     error_xpath = "./RESPONSE/TEXT"
        #     in_progress_string = "This scan has already been shared with the"
        #     in_progress_string += " Merchant account."
        #     response_xml = ET.fromstring(response.text.encode('utf8',
        #                                                       'ignore'))
        #     if response_xml.find(error_xpath).text == in_progress_string:
        #         print 'Scan share in progress'
        #         for i in range(0, 3):
        #             status_response = qc.get_pci_share_status(session,
        #                                                       qg_scan.scan_id,
        #                                                       merchant_user)
        #             status_xml = ET.fromstring(status_response.text.encode(
        #                 'utf8', 'ignore'
        #             ))
        #             if status_xml.find('./RESPONSE/SCAN/STATUS').text == \
        #                     'Finished':
        #                 print 'Scan ' + qg_scan.scan_id + \
        #                       ' shared with merchant account'
        #                 return
        #             time.sleep(720)
        #     exit(0)
    except Exception:
        traceback.print_exc()
        exit(2)
    finally:
        qc.logout(session)


if __name__ == '__main__':
    main()
