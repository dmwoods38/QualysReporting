import sys
import os
import qgreports.qualys_connector as qc
import qgreports.config.settings
import traceback
import json
import logging.config

__author__ = "StanPast"

user = qgreports.config.settings.QualysAPI['username']
password = qgreports.config.settings.QualysAPI['password']
scan_config = os.path.dirname(qgreports.config.__file__) + '/scan_config.json'

logging.config.fileConfig(os.path.join(os.path.dirname(qgreports.config.__file__),
                          'logging_config.ini'))
logger = logging.getLogger()


def main():
    # Add ips, add asset groups and schedule a scan
    with open(scan_config) as f:
        scan_entries = json.load(f)

    session = qc.login(user, password)

    try:
        res = qc.add_ips({
            "ips": ",".join(list(
                [str(scan['ips']).strip(",").strip() for scan in scan_entries if "ips" in scan]
            ))
        }, session)

        if "IPs successfully added to Vulnerability Management" not in res:
            logger.info('Unable to add IP')
            logger.debug('Unable to add IP: %s\n' % res)
    except Exception as e:
        traceback.print_exc()
        sys.exit(2)

    for entry in scan_entries:
        try:
            if "asset_group_title" in entry:
                res = qc.add_asset_group({"title": entry['asset_group_title']}, session)
                if "#####" not in res:
                    logger.info('Unable to add Asset Group')
                    logger.debug('Unable to add Asset Group: %s\n' % res)

            if "scan_title" in entry:
                res = qc.schedule_scan({"scan_title": entry['scan_title']}, session)
                if "#####" not in res:
                    logger.info('Unable to Schedule Scan')
                    logger.debug('Unable to Schedule Scan: %s\n' % res)

        except Exception as e:
            traceback.print_exc()
            sys.exit(2)

    qc.logout(session)



if __name__ == "__main__":
    main()
