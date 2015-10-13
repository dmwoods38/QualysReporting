#!/usr/local/bin/python
# Author: Dean Woods
# Created: 6/23/15
# Last modified: 7/6/15
# Description:
#     This is intended to download the current scan schedule from LNE's 
#     Qualys account. You must have a valid login with read privs in 
#     order to use this.
import getpass
import requests
import getopt
import sys
import xml.etree.ElementTree as ET
import datetime

qualys_api_url = "https://qualysapi.qualys.com"
session_cookie = None


def print_usage():
    print "Usage: ./get_scan_schedule.py [-o outfile] [-h]"
    print "\t-o outfile: File to write schedule to in CSV format."
    print "\t-h: displays usage."


#
def qualys_login():
    pass


# Params: Strings for username and password
# Return: Returns XML from the request 
def qualys_api_request(params, auth, dest_url="/api/2.0/fo/schedule/scan"): 
    h = {"X-Requested-With": "Python"}
    print "Making API call..."
    r = requests.get(qualys_api_url+dest_url, auth=auth, params=params,headers=h)
    if r.status_code == 401:
        print "There was an error logging you in, check your password?"
        sys.exit(2)
    elif r.status_code == 404:
        print "Page not found error, check the URL?"
        sys.exit(2)
    print "Call made to " + r.url
    return r
    #return ET.fromstring(r.content)


#Translates integer days 0-6 to human-friendly days
def int_day_to_str(day):
    if day == '0':
        return 'Sunday'
    elif day == '1':
        return 'Monday'
    elif day == '2':
        return 'Tuesday'
    elif day == '3':
        return 'Wednesday'
    elif day == '4':
        return 'Thursday'
    elif day == '5':
        return 'Friday'
    elif day == '6':
        return 'Saturday'
    else:
        print day
        raise ValueError("Unexpected day number")


# Params: Takes in an xml tag with the schedule frequency from Qualys 
# Return: Returns a more human-friendly schedule as a string
def build_freq_str(sched):
    freq = sched[0]
    if freq.tag == 'WEEKLY':
        day_of_week = int_day_to_str(freq.attrib.get('weekdays'))
        weekly_freq = freq.attrib.get('frequency_weeks')
        return "Every " + weekly_freq + " week(s) on " + day_of_week
    elif freq.tag == 'MONTHLY':
        monthly_freq = freq.attrib.get('frequency_months')
        s = "Every " + monthly_freq + " month(s) on "
        if freq.attrib.get('day_of_week') != None:
            day_of_week = int_day_to_str(freq.attrib.get('day_of_week'))
            week_of_month = freq.attrib.get('week_of_month')
            s = s + day_of_week + " of week " + week_of_month
        else:
            s = s + "day " + freq.attrib.get('day_of_month')
        return s
    elif freq.tag == 'DAILY':
        days = freq.attrib.get('frequency_days')
        if int(days) % 7 == 0:
            d = sched.find(".//NEXTLAUNCH_UTC").text
            day = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
            day_of_week = int_day_to_str(str((day.weekday() + 1) %7))
            weekly_freq = str(int(days) / 7)
            return "Every " + weekly_freq + " week(s) on " + day_of_week
        else:
            return "Every " + days + " days"
    else:
        print freq.tag
        raise ValueError("Schedule did not have a recognized Frequency")


# Params: Takes in some sort of schedule object list
#         Need to determine what this will look like
def schedule_change_control(schedules):
    print "hello3"


# Params: Takes in the XML for the schedule
# Return: Returns a dict list
#         Each dict has: Scan Title, Target IPs, Asset Group Name(s),
#                        Start Time, Timezone, Schedule Frequency
def parse_schedule(schedule_xml):
    schedules = []
    for i in schedule_xml.findall(".//SCAN"):
        title = i.find("./TITLE").text
        target = i.find("./TARGET").text
        try:
            ags_nodes = i.find("./ASSET_GROUP_TITLE_LIST")
            ags_nodes = ags_nodes.findall("./ASSET_GROUP_TITLE")
            ags =  [x.text for x in ags_nodes]
        except AttributeError:
            ags = ["None"]
        sched = i.find("./SCHEDULE")
        freq_str = build_freq_str(sched)
        time = sched.find("./START_HOUR").text + ":"
        minute = sched.find("./START_MINUTE").text
        time = time + minute if len(minute) == 2 else time + '0' + minute
        timezone = sched.find("./TIME_ZONE").find("./TIME_ZONE_DETAILS").text
        schedule = {"Title" : title, "Targets": target}
        schedule.update({"Address Groups": ", ".join(ags), "Frequency": freq_str})
        schedule.update({"Time": time, "Timezone": timezone})
        schedules.append(schedule)
    return schedules


# Params:
#        str file - File to write to
#        dict[] schedules - schedule info
#        str[] columns - column titles to use 
#        str sep - separator to use for CSV
#					Note: this won't work properly with ',' as a separator atm
def write_csv(file, schedules, columns=None, sep=';'):
    try:
        f = open(file, 'w')
    except Exception:
        print "Could not open file"
        sys.exit(2)
    buf = "sep=" + sep + "\n"
    if columns != None:
        buf = buf + sep.join(columns) + "\n"
    for schedule in schedules:
        buf = buf + schedule.get('Title') + sep
        buf = buf + schedule.get('Address Groups') + sep
        buf = buf + schedule.get('Targets') + sep
        buf = buf + schedule.get('Frequency') + sep
        buf = buf + schedule.get('Time') + sep
        buf = buf + schedule.get('Timezone') + sep
        buf += "\n"
    f.write(buf.encode('ascii','ignore'))
    f.close()


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:")
    except getopt.GetoptError as err:
        print str(err)
        print_usage()
        sys.exit(2)
    if len(opts) < 1:
        s = "Sorry :/ this script doesn't do anything useful right now"
        s += " if you don't specify an outfile with -o"
        print s
        print_usage()
        sys.exit()
    outfile = None
    for o, a in opts:
        if o == '-o':
            outfile = a
        elif o == '-h':
            print_usage()
            sys.exit()
        else:
            assert False, "unhandled option"
    user = raw_input("Qualys username: ")
    pw = getpass.getpass()

    query_params = {"action":"list", "active":"1"}
    tree = ET.fromstring(qualys_api_request(query_params, (user,pw)).content)
    schedules = parse_schedule(tree)
    if outfile is not None:
        cols = ['Scan Name', 'Address Groups', 'IPs', 'Frequency', 'Time']
        cols.append('Timezone')
        write_csv(outfile, schedules, columns=cols)

if __name__ == "__main__":
    main()
