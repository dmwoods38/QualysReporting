import os
import requests
import sys
import xml.etree.ElementTree as ET
import datetime
import time
import subprocess
import qgreports.config.settings
import certifi
import logging.config

__author__ = "dmwoods38"
qualys_api_url = qgreports.config.settings.QualysAPI['url']
xreq_header = {"X-Requested-With": "Python"}
session_path = "/api/2.0/fo/session/"		
debug = qgreports.config.settings.debug

#init logger
logging.config.fileConfig(os.path.join(os.path.dirname(qgreports.config.__file__),
                          'logging_config.ini'))  
logger = logging.getLogger()

# Params: Strings for username and password
# Optional headers to include with login request
# Return: Returns session 
def login(username, password, headers=xreq_header, params=None):
    if params is None:
        params = {}
    params.update({"action": "login", "username": username,
                   "password": password})
    r = requests.Session()
    s = request(params, r, session_path, headers=headers, verb="post")
    if check_status(s):
        logger.info('Successfully logged in')
        return r
    else:
        logger.info('There was an error logging you in')
        if debug:
            logger.info(s.text)


# Params: Session to logout of 
#         Optional headers to include with logout request
def logout(session, headers=xreq_header, params=None):
    if params is None:
        params = {}
    params.update({"action": "logout"})
    s = request(params, session, session_path, headers=headers, verb="post")
    if check_status(s):
        logger.info('Successfully logged out')
    else:
        logger.info('There was an error logging you out')


# Params: Takes in a Response object
# Description: Error checking for the response codes
def check_status(response):
    if response.status_code == 200:
        return True
    else:
        logger.info('Error with the request')
        logger.info('Status code: ' + str(response.status_code))
        return False


# Params
def request(params, session, dest_url, verb='POST', headers=xreq_header,
                data=""):
    # sleep for rate limiting
    time.sleep(3)
    logger.debug('HTTP Verb' + verb)
    logger.debug('URL: ' + qualys_api_url+dest_url)
    logger.debug('Params: ' + str(params))
    
    try:
        if verb.upper() == 'GET':
            s = session.get(qualys_api_url+dest_url, params=params,
                            headers=headers, verify=certifi.where())
        elif verb.upper() == 'POST':
            s = session.post(qualys_api_url+dest_url, params=params,
                             headers=headers, data=data,
                             verify=certifi.where())
        else:
            logger.info('Unsupported HTTP verb: ' + verb)
            sys.exit(2)
        logger.debug('status_code: ' + str(s.status_code))
    except Exception as e:
        logger.info(e)
        logger.info('Retrying...')
        try:
            s = session.post(qualys_api_url+dest_url, params=params, headers=headers, data=data)
        except Exception as e:
            logger.info(e)
            sys.exit(2)
    return s


# Return: Returns XML with the VM scan list
def get_scans(session, params=None):
    if params is None:
        params = {}
    params.update({"action": "list"})
    dest_url = "/api/2.0/fo/scan/"
    response = request(params, session, dest_url)
    if check_status(response):
        return response.text
    else:
        logger.info('Error retrieving scan list')
        sys.exit(2)


# Takes and updates scan objects.
def get_scan_refs(scans, session, params=None, scans_list=None):
    if params is None:
        params = {}
    if scans_list is None:
        scans_list = get_scans(session, params)
    scan_xml = ET.fromstring(scans_list.encode('utf8', 'ignore'))
    scan_xpath = "./RESPONSE/SCAN_LIST/SCAN/"
    for scan in scans:
        scan_name = scan.scan_name
        scan_list = [scan_xml.find(scan_xpath + "[TITLE='" + scan_name + "']")]

        for node in scan_list:
            if node is not None and int(node.find("./PROCESSED").text):
                scan.scan_state = 'processed'
                scan.scan_id = node.find("./REF").text
            elif node is None:
                scan.scan_state = 'noscan'
            else:
                scan.scan_state = 'unprocessed'
                scan.scan_id = node.find("./REF").text
        logger.debug('Scan state: ' + scan.scan_state)
        logger.debug('Scan name: ' + scan_name)


def get_asset_group_ips(scheduled_reports, session, params=None):
    if params is None:
        params = {}
    params.update({"action": "list"})
    dest_url = "/api/2.0/fo/asset/group/"
    asset_group_xpath = "./RESPONSE/ASSET_GROUP_LIST/ASSET_GROUP"
    ips_xpath = "./IP_SET"

    response = request(params, session, dest_url)
    asset_group_list_xml = ET.fromstring(
        response.text.encode('utf8', 'ignore'))

    # Go through the asset groups and find the IPs
    for report in scheduled_reports:
        asset_groups = report.asset_groups.split(',')
        for asset_group in asset_groups:
            for asset_group_xml in \
                    asset_group_list_xml.findall(asset_group_xpath):
                # check
                if asset_group_xml.find("./TITLE").text == asset_group:
                    ip_set_xml = asset_group_xml.find(ips_xpath)
                    #WARNING - second if inside for - is using continue possible?
                    if report.asset_ips != '' and report.asset_ips is not None:
                        report.asset_ips += ','
                    if report.asset_ips is None:
                        report.asset_ips = ''
                    ips = [i.text for i in ip_set_xml.getchildren()]
                    report.asset_ips += ','.join(ips)
        if (report.asset_ips == '' or report.asset_ips is None) and \
                (report.asset_groups != '' and
                         report.asset_groups is not None):
            logger.info('No ips found for: ' + report.asset_groups)


# TODO: Add support for reports with multiple scan refs.
# Description: Launches scan reports and then returns the refs
#              with the corresponding report ids
def launch_scan_reports(scheduled_reports, session, params=None):
    if params is None:
        params = {}
    params.update({"report_type": "Scan", "action": "launch"})
    params.update({"template_id":
                       qgreports.config.settings.QualysAPI['scan_template']})
    dest_url = "/api/2.0/fo/report/"
    item_xpath = "./RESPONSE/ITEM_LIST/ITEM"
    max_num_xpath = "./RESPONSE/TEXT"
    max_report_string = "Max number of allowed reports"

    for report in scheduled_reports:
        if report.scan.scan_state.lower() == 'processed':
            #WARNING - second if inside for - is using continue possible?
            if 'ip_restriction' in params:
                del params['ip_restriction']
            if report.asset_ips is not None and report.asset_ips != "":
                params.update({"ip_restriction": report.asset_ips})
            params.update({"report_refs": report.scan.scan_id})
            params.update({"output_format": report.output})

            # make request then parse xml for report id
            response = request(params, session, dest_url)
            report_xml = ET.fromstring(response.text.encode('utf8', 'ignore'))
            while max_report_string in report_xml.find(max_num_xpath).text:
                logger.debug('Max reports running already. Waiting 2 min...')
                time.sleep(120)
                response = request(params, session, dest_url)
                report_xml = ET.fromstring(response.text.encode('utf8',
                                                                'ignore'))
            items = report_xml.findall(item_xpath)
            for item in items:
                if item.find("./KEY").text.upper() == "ID":
                    report.report_id = item.find("./VALUE").text
                    break
            logger.debug(response.text)
        else:
            with open(qgreports.config.settings.unprocessed_log, "a") as f:
                f.write("Unprocessed for " + datetime.date.today().__str__())
                f.write(report.email.subject)


# Check that the report is finished before we try to download them.
def check_report_status(scheduled_reports, session):
    params = {"action": "list"}
    dest_url = "/api/2.0/fo/report/"
    report_list = request(params, session, dest_url)
    report_list_xml = ET.fromstring(report_list.text)
    # TODO add checking for report share limit and automatic deletion from the queue.
    # report_limit = "Your Report Share user limit has been reached. " \
    #                "This report will not be saved."
    # report_limit_xpath = "./RESPONSE/TEXT"

    report_xpath = "./RESPONSE/REPORT_LIST/REPORT"
    for report in scheduled_reports:
        for report_xml in report_list_xml.findall(report_xpath):
            if report_xml.find("./ID").text == report.report_id:
                state = report_xml.find("./STATUS/STATE").text
                #WARNING - second if inside for - is using continue possible?
                if state == "Finished":
                    report.report_status = 'Finished'
                elif state == "Running" or state == "Submitted":
                    report.report_status = 'Unfinished'
                else:
                    logger.info('The report will not complete')
                    logger.info('Report status: ' + state)
                    sys.exit(2)


# Download reports
def get_reports(scheduled_reports, session, add_timestamp=True,
                no_clobber=False):
    params = {"action": "fetch"}
    dest_url = "/api/2.0/fo/report/"
    report_path = qgreports.config.settings.report_folder

    if add_timestamp:
        today = datetime.date.today().__str__()
        report_suffix = ' ' + today
    else:
        report_suffix = ''
    keepcharacters = (' ', '.', '_', '/', '-')
    print "Trying to get reports..."
    for report in scheduled_reports:
        if report.report_id is None:
            continue
        params.update({"id": report.report_id})
        report_name = ''.join(c for c in report.email.subject if c.isalnum() or
                              c in keepcharacters)
        report_name = report_name.replace('/', '_') + report_suffix

        filetype = '.' + report.output
        report.report_filename = report_path + report_name + filetype
        if no_clobber:
            with open(report.report_filename, 'ab') as f:
                response = request(params, session, dest_url)
                check_status(response)
                f.write(response.content)
        else:
            with open(report.report_filename, 'wb') as f:
                response = request(params, session, dest_url)
                check_status(response)
                f.write(response.content)


# Returns API scan results, not the same as a scan report. Much less detail.
def get_scan_results(scans_with_refs, session, scans_with_files,
                            folder="/root/reports/",
                            format="csv", params={}):
    params.update({"action": "fetch", "mode": "brief",
                   "output_format": format})
    dest_url = "/api/2.0/fo/scan/"
    processed = scans_with_refs['processed']
    unprocessed = scans_with_refs['unprocessed']
    for scan in processed:
        for ref in processed[scan]:
            params.update({"scan_ref":ref})
            response = request(params, session, dest_url)
            file = scans_with_files[scan] if scans_with_files[scan] else scan
            filename = folder + file
            filename = filename + "_" +datetime.date.today().__str__()
            filename = filename + "." + format
            with open(filename, "a") as f:
                f.write(response.text)

    if len(unprocessed):
        with open("/root/unprocessed.log", "a") as f:
            f.write("Unprocessed for " + datetime.date.today().__str__())
            f.write(str(unprocessed))


def get_pci_share_status(session, scan_id, merchant_username, params=None):
    if params is None:
        params = {}
    params.update({'action': 'status', 'scan_ref': scan_id,
                   'merchant_username': merchant_username})
    dest_url = '/api/2.0/fo/scan/pci'
    return request(params, session, dest_url)
