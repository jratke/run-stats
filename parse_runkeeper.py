#!/usr/bin/env python

import argparse
from csv import DictReader
from datetime import date, datetime, timedelta

# column position constants
AVG_PACE = 'Average Pace'
AVG_SPEED = 'Average Speed (mph)'
CLIMBED = 'Climb (ft)'
AVG_HR = 'Average Heart Rate (bpm)'

# python 2.6 doesn't have timedelta.total_seconds(), so use this
def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 1e6) / 1e6

# return a time delta object from a given string MM:SS or HH:MM:SS
def get_duration(string):
    parts = string.split(":")
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts[0], parts[1]
    elif len(parts) == 3:
        hours, minutes, seconds = parts[0], parts[1], parts[2]
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))

# Scan through cvs file and if a row matches the selector lambda function
# (taking params: row, when, duration, pace) then accumulate stats
# regarding that activity.
#
# Returns: result dictionary with stats for the matching activites.
def scan(selector):
    result = dict(dist_sum=0.0, dist_long=0.0, count=0, out_count=0,
                  fastest=timedelta().max, slowest=timedelta(),
                  time_sum=timedelta(), time_long=timedelta(),
                  climbed=0.0, cal=0.0, cal_max=0.0)
    pace_sum = timedelta()
    pace_sum_count = 0

    csv_file = DictReader(open(args.file,'rb'),delimiter=',')
    for row in csv_file:
        activity_time = datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S")
        duration = get_duration(row['Duration'])

        # TODO: probably don't need to make a datetime here just to parse MM:SS
        if row[AVG_PACE]:
            #pace_dt = datetime.strptime(row[AVG_PACE], "%M:%S")
            #pace = timedelta(minutes=pace_dt.minute, seconds=pace_dt.second)
            pace = get_duration(row[AVG_PACE])
        else:
            pace = timedelta()

        if selector(row, activity_time, duration, pace):
            dist = float(row['Distance (mi)'])
            result['dist_sum'] += dist
            result['dist_long'] = max(dist, result['dist_long'])
            result['count'] += 1
            result['time_sum'] += duration
            result['time_long'] = max(duration, result['time_long'])
            if row[CLIMBED]:
                result['climbed'] += float(row[CLIMBED])
            result['cal'] += float(row['Calories Burned'])
            result['cal_max'] = max(float(row['Calories Burned']), result['cal_max'])
            if row['GPX File'] != '':
                result['out_count'] += 1
            result['fastest'] = min(pace, result['fastest'])
            result['slowest'] = max(pace, result['slowest'])
            pace_sum += pace
            pace_sum_count += 1

    if pace_sum_count > 0:
        result['avg_pace'] = timedelta(seconds = (total_seconds(pace_sum) / pace_sum_count))
    else:
        result['avg_pace'] = timedelta()
    return result

# for a given "time_selector" lambda function taking in a datetime (which usually matches a
# particuar year or all years of the csv data), if the datetime selector
# matches, then accumulate various stat dictionaries for different activity types, and print
# those stat summaries
#
def show_summary(time_selector):
    if args.showrun:
        runs = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Running")
    #if args.showwalk:
    walks   = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Walking")
    #if args.showcycle:
    cycling   = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Cycling")
    #if args.showother:
    others   = scan(lambda row,when,dur,pace:
                  time_selector(when) and 
                  (row['Type']!="Running" and row['Type']!="Walking" and row['Type']!="Cycling"))
    #if args.showall:
    all   = scan(lambda row,when,dur,pace: time_selector(when))

    # TODO: format this dynamically taking into account which activities to display.
    print 'Dist: {0:17.2f} {1:17.2f} {2:17.2f} {3:17.2f} {4:17.2f}'.format(runs['dist_sum'], walks['dist_sum'], cycling['dist_sum'], others['dist_sum'], all['dist_sum'])
    print 'Long: {0:17.2f} {1:17.2f} {2:17.2f} {3:17.2f} {4:17.2f}'.format(runs['dist_long'], walks['dist_long'], cycling['dist_long'], others['dist_long'], all['dist_long'])
    print 'Pace: {0:>17s} {1:>17s} {2:>17s}'.format(runs['avg_pace'], walks['avg_pace'], cycling['avg_pace'])
    # TODO: If fastest is max, just leave it blank
    print 'Fast: {0:>17s} {1:>17s} {2:>17s}'.format(runs['fastest'], walks['fastest'], cycling['fastest'])
    print 'Slow: {0:>17s} {1:>17s} {2:>17s}'.format(runs['slowest'], walks['slowest'], cycling['slowest'])
    print 'Count:{0:17d} {1:17d} {2:17d} {3:17d} {4:17d}'.format(runs['count'], walks['count'], cycling['count'], others['count'], all['count'])
    print 'Outdoor:{0:15d} {1:17d} {2:17d} {3:17d} {4:17d}'.format(runs['out_count'], walks['out_count'], cycling['out_count'], others['out_count'], all['out_count'])
    print 'Time: {0:>17s} {1:>17s} {2:>17s} {3:>17s} {4:>17s}'.format(runs['time_sum'], walks['time_sum'], cycling['time_sum'], others['time_sum'], all['time_sum'])
    print 'Long: {0:>17s} {1:>17s} {2:>17s} {3:>17s} {4:>17s}'.format(runs['time_long'], walks['time_long'], cycling['time_long'], others['time_long'], all['time_long'])
    print 'Climb:{0:17.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(runs['climbed'], walks['climbed'], cycling['climbed'], others['climbed'], all['climbed'])
    print 'Cals: {0:17.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(runs['cal'], walks['cal'], cycling['cal'], others['cal'], all['cal'])
    print 'MaxCals: {0:14.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(runs['cal_max'], walks['cal_max'], cycling['cal_max'], others['cal_max'], all['cal_max'])

parser = argparse.ArgumentParser(description='Parses and displays stats from RunKeeper exported data.')
parser.add_argument("-r","--run", help="show running stats (the default action)",
                    action="store_true", dest="showrun",   default=True)
parser.add_argument("-w","--walk", help="show walking stats",
                    action="store_true", dest="showwalk",  default=False)
parser.add_argument("-c","--cycle", help="show cycling stats",
                    action="store_true", dest="showcycle", default=False)
parser.add_argument("-o","--other", help="show all other stats",
                    action="store_true", dest="showother", default=False)
parser.add_argument("-a","--all", help="show combined total stats",
                    action="store_true", dest="showall",   default=False)
parser.add_argument("-f","--file", help="specify Runkeeper .csv data file",
                    default="cardioActivities.csv")
# TODO: add years option or other way to select time frame

args = parser.parse_args()

# assume first row has the field names, which it should.  This row then is not in the csv_file data.
csv_file = DictReader(open(args.file, 'rb'), delimiter=',')
prev = []

#csv_rows = sum(1 for line in csv_file)
#print 'length of csv dict (data rows): {0:d}'.format(csv_rows)
# need to reset somehow if we do that

earliest_year = date.today().year
#print 'first row: '
#print csv_file[0]
#print 'last row: '
#print csv_file[csv_rows-1]

for row in csv_file:
    #print row
    when = datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S")
    #print "year ", when.year
    earliest_year = min(earliest_year, when.year)
    if row == prev:
        print "Duplicate row: ", row
    prev = row

for year in range(earliest_year, date.today().year + 1):
    print '{0:4d}  {1:>17} {2:>17} {3:>17} {4:>17} {5:>17}'.format(year,'Run','Walk','Cycle','Other','All')
    show_summary(lambda t: t.year == year)
    print ""

print 'Total {0:>17} {1:>17} {2:>17} {3:>17} {4:>17}'.format('Run','Walk','Cycle','Other','All')
show_summary(lambda t: t.year >= earliest_year and t.year <= date.today().year + 1)
