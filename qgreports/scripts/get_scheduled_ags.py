import datetime
import traceback
import qgreports.config.settings
from qgreports.objects import Report
import qgreports.qualys_connector as qc
import sys
import xml.etree.ElementTree as ET

username = qgreports.config.settings.QualysAPI['username']
password = qgreports.config.settings.QualysAPI['password']
dest_url = '/api/2.0/fo/schedule/scan'
outfile = qgreports.config.settings.report_folder + 'scheduled_ags.csv'


# Translates integer days 0-6 to human-friendly days
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
        if freq.attrib.get('day_of_week') is not None:
            day_of_week = int_day_to_str(freq.attrib.get('day_of_week'))
            week_of_month = freq.attrib.get('week_of_month')
            if week_of_month == '1':
                week_of_month_str = 'the 1st'
            elif week_of_month == '2':
                week_of_month_str = 'the 2nd'
            elif week_of_month == '3':
                week_of_month_str = 'the 3rd'
            elif week_of_month == '4':
                week_of_month_str = 'the 4th'
            elif week_of_month == '5':
                week_of_month_str = 'the last'
            else:
                raise ValueError("Unexpected week of the month")
            s = s + week_of_month_str + ' '
            s = s + day_of_week + " of the month"
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


# Params: Takes in the XML for the schedule
# Return: Returns a dict list
#         Each dict has: Scan Title, Target IPs, Asset Group Name(s),
#                        Start Time, Timezone, Schedule Frequency
def parse_schedule(schedule_xml, session):
    schedules = []
    for i in schedule_xml.findall(".//SCAN"):
        title = i.find("./TITLE").text
        try:
            ags_nodes = i.find("./ASSET_GROUP_TITLE_LIST")
            ags_nodes = ags_nodes.findall("./ASSET_GROUP_TITLE")
            ags = [x.text for x in ags_nodes]
            ags = [Report(asset_groups=ag) for ag in ags]
        except AttributeError:
            ags = [None]
        sched = i.find("./SCHEDULE")
        freq_str = build_freq_str(sched)
        time = sched.find("./START_HOUR").text + ":"
        minute = sched.find("./START_MINUTE").text
        time = time + minute if len(minute) == 2 else time + '0' + minute
        timezone = sched.find("./TIME_ZONE").find("./TIME_ZONE_DETAILS").text
        next_launch = sched.find("./NEXTLAUNCH_UTC").text
        schedule = {"Title": title}
        schedule.update({"Asset Groups": ags, "Frequency": freq_str})
        schedule.update({"Time": time, "Timezone": timezone})
        schedule.update({"Next Launch (UTC)": next_launch})
        schedules.append(schedule)
    ag_schedules = []
    all_ags = [ags for schedule in schedules
               for ags in schedule.get('Asset Groups')
               if ags is not None]
    qc.get_asset_group_ips(all_ags, session)
    for schedule in schedules:
        ags = schedule.get('Asset Groups')
        for ag in ags:
            if ag is None:
                continue
            print ag.asset_groups

            ag_schedule = {'Frequency': schedule.get('Frequency')}
            ag_schedule.update({'Time': schedule.get('Time'),
                                'Timezone': schedule.get('Timezone'),
                                'Next Launch (UTC)':
                                    schedule.get('Next Launch (UTC)')})
            ag_schedule.update({'Asset Group': ag.asset_groups,
                                'IPs': ag.asset_ips})
            ag_schedules.append(ag_schedule)
    return ag_schedules


# Params:
#        str file - File to write to
#        dict[] schedules - schedule info
#        str[] columns - column titles to use 
#        str sep - separator to use for CSV
# 		 Note: this won't work properly with ',' as a separator atm
def write_csv(filename, schedules, columns=None, sep=';'):
    try:
        f = open(filename, 'w')
    except Exception:
        print "Could not open file"
        sys.exit(2)
    buf = "sep=" + sep + "\n"
    if columns is not None:
        buf = buf + sep.join(columns) + "\n"
    for schedule in schedules:
        buf = buf + schedule.get('Asset Group') + sep
        buf = buf + schedule.get('IPs') + sep
        buf = buf + schedule.get('Frequency') + sep
        buf = buf + schedule.get('Time') + sep
        buf = buf + schedule.get('Timezone') + sep
        buf = buf + schedule.get('Next Launch (UTC)') + sep
        buf += "\n"
    f.write(buf.encode('ascii', 'ignore'))
    f.close()


def main():
    session = qc.login(username, password)
    try:
        query_params = {"action": "list", "active": "1"}
        tree = ET.fromstring(
            qc.request(query_params, session, dest_url).content)
        schedules = parse_schedule(tree, session)
        if outfile is not None:
            cols = ['Asset Group', 'IPs', 'Frequency', 'Time',
                    'Timezone', 'Next Launch (UTC)']
            write_csv(outfile, schedules, columns=cols)
    except Exception:
        traceback.print_exc()
        sys.exit(2)
    finally:
        qc.logout(session)


if __name__ == "__main__":
    main()
