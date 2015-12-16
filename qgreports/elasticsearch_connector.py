import json
import csv
import qgreports.objects
import qgreports.config.settings
import elasticsearch
from requests_aws4auth import AWS4Auth
from qgreports.utils.results_methods import parse_csv_scan_header
__author__ = 'dmwoods38'

es_mapping_path = os.path.dirname(os.path.realpath(__file__))
vuln_mapping_path = es_mapping_path + '/config/qualys-vuln-mapping.json'
scan_mapping_path = es_mapping_path + '/config/qualys-scan-mapping.json'
es_config = qgreports.config.settings.ELASTICSEARCH


def initialize_es():
    # Check ES config from settings
    if es_config['host'] != '':
        if es_config['aws_auth']:
            # Do aws auth stuff here..
            aws_access_key = qgreports.config.settings.AWS['access_key']
            aws_secret_key = qgreports.config.settings.AWS['secret_key']
            aws_region = qgreports.config.settings.AWS['region']
            auth = AWS4Auth(aws_access_key, aws_secret_key, aws_region, 'es')
            conn = elasticsearch.connection.RequestsHttpConnection
            es = elasticsearch.Elasticsearch(host=es_config['host'],
                                             port=es_config['port'],
                                             http_auth=auth,
                                             use_ssl=es_config['use_ssl'],
                                             connection_class=conn)
        else:
            es = elasticsearch.Elasticsearch(host=es_config['host'],
                                             port=es_config['port'])
    else:
        es = elasticsearch.Elasticsearch()
    with open(vuln_mapping_path, 'r') as f:
        es.indices.create(index='vulnerability')
        es.indices.put_mapping(index='vulnerability',
                               doc_type='qualys',
                               body=json.dumps(json.load(f)))
    with open(scan_mapping_path, 'r') as f:
        es.indices.create(index='scan_metadata')
        es.indices.put_mapping(index='scan_metadata',
                               doc_type='qualys',
                               body=json.dumps(json.load(f)))
    return es


# Parse CSV and send results into elasticsearch.
def es_scan_results(filename, es=None):
    with open(filename, 'r') as csvfile:
        if es is None:
            es = elasticsearch.Elasticsearch()
        csvreader = csv.reader(csvfile, dialect='excel')
        vulns = []

        for i in range(0, 5, 1):
            csvreader.next()
        scan_results = csvreader.next()
        scan_info = parse_csv_scan_header(scan_results)
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
        scan_info.update({'dead_hosts': dead_hosts,
                            'clean_hosts': clean_hosts})
        es.index(index='scan_metadata', doc_type='qualys',
                 id=scan_info['scan_ref'], body=scan_info)
        scan_metadata = {'scan_date': scan_info['scan_date'],
                         'scan_ref': scan_info['scan_ref']}
        for x in vulns:
            x.__dict__.update(scan_metadata)
            es.index(index='vulnerability', doc_type='qualys',
                     body=x.__dict__)

