import csv
import datetime
import qgreports.objects
import json
__author__ = 'dmwoods38'


# Parses CSV scan results and returns Vuln list.
def parse_scan_results(filename):
    pci_scope = True if filename.rsplit('/')[-1].split('-')[0].upper() == \
                        'PCI' else False
    scope = filename.rsplit('/')[-1].split('-')[1].upper()
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile, dialect='excel')
        vulns = []
        # Parse header information
        for i in range(0, 5, 1):
            csvreader.next()
        date_str, timezone = csvreader.next()[0].split('(')
        scan_date = datetime.datetime.strptime(date_str,
                                               '%m/%d/%Y at %H:%M:%S ')
        timezone = timezone.strip(')')

        csvreader.next()
        csvdictreader = csv.DictReader(csvfile, csvreader.next(),
                                       dialect='excel')

        # TODO: Change to be dict based.
        for row in csvdictreader:
            if row['QID'] is None:
                continue
            if row['DNS'].strip() == 'No registered hostname':
                dns = None
            else:
                dns = row['DNS']
            entry = qgreports.objects.Vuln(dns, row['IP'], row['OS'],
                                           row['QID'], row['Severity'],
                                           scan_date, timezone, pci_scope,
                                           scope)
            vulns.append(entry)

    return vulns


# Parse Qualys report scan header and return dict
def parse_csv_scan_header(row):
    date_str, scan_timezone = row[0].split('(')
    scan_date = date_str.strip()
    scan_timezone = scan_timezone.strip(')')
    active_hosts = row[1]
    total_hosts = row[2]
    scan_type = row[3]
    scan_status = row[4]
    reference = row[5]
    scanner_appliance = row[6]
    duration = row[7]
    scan_title = row[8]
    asset_groups = row[9]
    ips = row[10]
    excluded_ips = row[11]
    option_profile = row[12]
    return {'scan_date': scan_date, 'scan_timezone': scan_timezone,
            'active_hosts': active_hosts, 'total_hosts': total_hosts,
            'scan_type': scan_type, 'scan_status': scan_status,
            'reference': reference, 'duration': duration,
            'scanner_appliance': scanner_appliance, 'ips': ips,
            'scan_title': scan_title, 'asset_groups': asset_groups,
            'excluded_ips': excluded_ips, 'option_profile': option_profile}


# Parse CSV and return JSON for elasticsearch.
def es_scan_results(filename):
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile, dialect='excel')
        vulns = []
        # Parse header information
        date_str, report_timezone = csvreader.next()[1].split('(')
        report_date = date_str.strip()
        report_timezone = report_timezone.strip(')')
        for i in range(0, 4, 1):
            csvreader.next()
        scan_info = csvreader.next()
        header_info = parse_csv_scan_header(scan_info)
        csvreader.next()
        csvdictreader = csv.DictReader(csvfile, [x.replace(' ', '_').lower()
                                                 for x in csvreader.next()],
                                       dialect='excel')
        dead_hosts = None
        clean_hosts = None

        for row in csvdictreader:
            if row['qid'] is None:
                if 'hosts not scanned' in row['ip_status']:
                    dead_hosts = row['ip']
                elif 'No vulnerabilities' in row['ip_status']:
                    clean_hosts = row['ip']
                continue
            if row['dns'].strip() == 'No registered hostname':
                row['dns'] = None
            entry = qgreports.objects.Vuln(**row)
            vulns.append(entry)
        header_info.update({'dead_hosts': dead_hosts,
                            'clean_hosts': clean_hosts,
                            'report_date': report_date,
                            'report_timezone': report_timezone})
        json_report = header_info
        json_report.update({'vulns': [x.__dict__ for x in vulns]})
    return json.dumps(json_report)
