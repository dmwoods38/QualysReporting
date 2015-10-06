import qgreports.controllers
import qgreports.models
from sqlalchemy.orm import sessionmaker
# Script to add large amount of reports to the db from a JSON file.
# This will also fill in all the other necessary tables.
__author__ = 'dmwoods38'


def main():
    engine = qgreports.models.db_init()
    Session = sessionmaker(bind=engine)
    session = Session()

    # TODO: Get Distribution lists from some sort of file
    distribution_lists = {'list1': 'test@test.com, test2@mydomain.com'}
    distribution_lists.update(
        {'list2': 'elephant@heffalump.com, woosel@heffalump.com'})
    email_entries = []

    # TODO: Get scan info from some sort of files
    scans_list = ['scan1', 'scan2']
    scan_entries = []

    for list_name, email_list in distribution_lists.iteritems():
        email_entries.append(qgreports.models.QGEmail(email_list=email_list,
                                         list_name=list_name))
    session.add_all(email_entries)
    session.commit()

    for scan in scans_list:
        scan_entries.append(qgreports.models.QGScan(scan_title=scan))

    session.add_all(scan_entries)
    session.commit()

    # TODO: Then add report information.

    # At the very end commit the session.
    session.commit()

    # cleanup of connections.
    session.close()
    engine.dispose()

if __name__ == '__main__':
    main()
