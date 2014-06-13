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

def get_duration(string):
    parts = string.split(":")
    if len(parts) == 2:
        hours = 0
        minutes, seconds = parts[0], parts[1]
    elif len(parts) == 3:
        hours, minutes, seconds = parts[0], parts[1], parts[2]
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))

def scan(selector):
    result = dict(dist_sum=0.0, dist_long=0.0, count=0, out_count=0,
                  time_sum=timedelta(), time_long=timedelta(),
                  climbed=0.0, cal=0.0, cal_max=0.0)
    pace_sum = timedelta()
    result['fastest'] = timedelta().max
    result['slowest'] = timedelta()
    pace_sum_count = 0

    csv_file = DictReader(open(args.file,'rb'),delimiter=',')
    for row in csv_file:
        activity_time = datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S")
        duration = get_duration(row['Duration'])

        # TODO: probably don't need to make a datetime here just to parse MM:SS
        if row[AVG_PACE]:
            pace = datetime.strptime(row[AVG_PACE], "%M:%S")
            pace_td = timedelta(minutes=pace.minute, seconds=pace.second)
        else:
            pace_td = timedelta()

        if selector(row, activity_time, duration, pace_td):
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
            if pace_td < result['fastest']:
                result['fastest'] = pace_td
            if pace_td > result['slowest']:
                result['slowest'] = pace_td

            pace_sum += pace_td
            pace_sum_count += 1

    if pace_sum_count > 0:
        result['avg_pace'] = timedelta(seconds = (total_seconds(pace_sum) / pace_sum_count))
    else:
        result['avg_pace'] = timedelta()
    return result

def show_summary(time_selector):
    if args.showrun:
        rres = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Running")
    #if args.showwalk:
    wres   = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Walking")
    #if args.showcycle:
    cres   = scan(lambda row,when,dur,pace: time_selector(when) and row['Type'] == "Cycling")
    #if args.showother:
    ores   = scan(lambda row,when,dur,pace: 
                  time_selector(when) and 
                  (row['Type']!="Running" and row['Type']!="Walking" and row['Type']!="Cycling"))
    #if args.showall:
    ares   = scan(lambda row,when,dur,pace: time_selector(when))

    # TODO: format this dynamically taking into account which activities to display.
    #print '{0:4d}  {1:>17} {2:>17} {3:>17} {4:>17} {5:>17}'.format(year,'Run','Walk','Cycle','Other','All')
    print 'Dist: {0:17.2f} {1:17.2f} {2:17.2f} {3:17.2f} {4:17.2f}'.format(rres['dist_sum'], wres['dist_sum'], cres['dist_sum'], ores['dist_sum'], ares['dist_sum'])
    print 'Long: {0:17.2f} {1:17.2f} {2:17.2f} {3:17.2f} {4:17.2f}'.format(rres['dist_long'], wres['dist_long'], cres['dist_long'], ores['dist_long'], ares['dist_long'])
    print 'Pace: ',rres['avg_pace']
    print 'Fast: ',rres['fastest']
    print 'Slow: ',rres['slowest']
    print 'Count:{0:17d} {1:17d} {2:17d} {3:17d} {4:17d}'.format(rres['count'], wres['count'], cres['count'], ores['count'], ares['count'])
    print 'Outdoor:{0:15d} {1:17d} {2:17d} {3:17d} {4:17d}'.format(rres['out_count'], wres['out_count'], cres['out_count'], ores['out_count'], ares['out_count'])
    print 'Time: {0:>17s} {1:>17s} {2:>17s} {3:>17s} {4:>17s}'.format(rres['time_sum'], wres['time_sum'], cres['time_sum'], ores['time_sum'], ares['time_sum'])
    print 'Long: {0:>17s} {1:>17s} {2:>17s} {3:>17s} {4:>17s}'.format(rres['time_long'], wres['time_long'], cres['time_long'], ores['time_long'], ares['time_long'])
    print 'Climb:{0:17.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(rres['climbed'], wres['climbed'], cres['climbed'], ores['climbed'], ares['climbed'])
    print 'Cals: {0:17.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(rres['cal'], wres['cal'], cres['cal'], ores['cal'], ares['cal'])
    print 'MaxCals: {0:14.0f} {1:17.0f} {2:17.0f} {3:17.0f} {4:17.0f}'.format(rres['cal_max'], wres['cal_max'], cres['cal_max'], ores['cal_max'], ares['cal_max'])
    print ""

parser = argparse.ArgumentParser(description='Parses and displays stats from RunKeeper exported data.')
parser.add_argument("-r","--run",   help="show running stats (the default action)",
                    action="store_true", dest="showrun",   default=True)
parser.add_argument("-w","--walk",  help="show walking stats",
                    action="store_true", dest="showwalk",  default=False)
parser.add_argument("-c","--cycle", help="show cycling stats",
                    action="store_true", dest="showcycle", default=False)
parser.add_argument("-o","--other", help="show all other stats",
                    action="store_true", dest="showother", default=False)
parser.add_argument("-a","--all",   help="show combined total stats",
                    action="store_true", dest="showall",   default=False)
parser.add_argument("-f","--file",  help="specify Runkeeper .csv data file",
                    default="cardioActivities.csv")
# TODO: add years option or other way to select time frame

args = parser.parse_args()

# assume first row has the field names, which it should.  This row then is not in the csv_file data.
csv_file = DictReader(open(args.file,'rb'),delimiter=',')
prev = []
oldest_year = date.today().year
for row in csv_file:
    when = datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S")
    oldest_year = min(oldest_year, when.year)
    if row == prev:
        print "Duplicate row: ", row
    prev = row

for year in range(oldest_year,date.today().year + 1):
    print '{0:4d}  {1:>17} {2:>17} {3:>17} {4:>17} {5:>17}'.format(year,'Run','Walk','Cycle','Other','All')
    show_summary(lambda t: t.year == year)

print 'Total {0:>17} {1:>17} {2:>17} {3:>17} {4:>17}'.format('Run','Walk','Cycle','Other','All')
#show_summary(lambda t: t.year >= 2013 and t.year <= 2014)
show_summary(lambda t: t.year >= oldest_year and t.year <= date.today().year + 1)
