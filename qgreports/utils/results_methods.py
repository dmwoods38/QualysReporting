import csv
import datetime
import qgreports.objects
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

