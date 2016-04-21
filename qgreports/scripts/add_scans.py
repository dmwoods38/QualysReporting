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
        res = qc.add_ips(session, {
            "ips": ",".join(list(
                [str(scan['ips']).strip(",").strip() for scan in scan_entries if "ips" in scan]
            ))
        })

        if "IPs successfully added to Vulnerability Management" not in res:
            logger.info('Unable to add IPs')
            logger.debug('Unable to add IPs: %s\n' % res)
        if "IPs successfully added to Vulnerability Management" in res:
            logger.info('IPs have been added')
            logger.debug('IPs have been added: %s\n' % res)

    except Exception as e:
        traceback.print_exc()
        sys.exit(2)

    for entry in scan_entries:
        try:

            if "asset_group_title" in entry:
                res = qc.add_asset_group(session, {"title": entry['asset_group_title'], "ips": entry['ips']})
                if "already exists. Please use a different title" in res:
                    logger.info('An asset group with that title already exists')
                    logger.debug('An asset group with that title already exists: %s\n' % res)
                if "Asset Group successfully added." not in res and "already exists. Please use a different title" not in res:
                    logger.info('Unable to add Asset Group')
                    logger.debug('Unable to add Asset Group: %s\n' % res)
                if "Asset Group successfully added." in res:
                    logger.info('Asset Group successfully added')
                    logger.debug('Asset Group successfully added: %s\n' % res)

            if "scan_title" in entry:
                res = qc.schedule_scan(session, {"scan_title": entry['scan_title'], "active": "1", "option_id": entry['option_profile_id'],
                                                 "occurrence": "monthly", "frequency_months": "1","day_of_month": entry['day_of_month'],
                                                 "time_zone_code": "US-CA", "observe_dst": "yes", "start_hour": "14",
                                                 "start_minute": "0","asset_groups": entry['asset_group_title']})
                if "New scan scheduled successfully" not in res:
                    logger.info('Unable to add new scan')
                    logger.debug('Unable to add new scan: %s\n' % res)
                if "New scan scheduled successfully" in res:
                    logger.info('New scan scheduled successfully')
                    logger.debug('New scan scheduled successfully: %s\n' % res)

        except Exception as e:
            traceback.print_exc()
            sys.exit(2)

    qc.logout(session)



if __name__ == "__main__":
    main()