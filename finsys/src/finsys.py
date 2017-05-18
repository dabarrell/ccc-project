
import couchdb
import sys, os
import datetime as dt
import time, re

def main():
    for item in generate_hourly_stats('2017-05-08 00:00:00','2017-05-11 03:00:00'):
        print item[0], item[1], item[2]['usdjpy']

def created_at_to_datetime(string):
    f = '%a %b %d %H:%M:%S %Y'
    assert '+0000' in string, 'twitter date unexpected utc offset'
    s = string.replace(' +0000','')
    tweet_time = dt.datetime.strptime(s,f)
    # adjust tweet time for utc offset
    return tweet_time + dt.timedelta(seconds=get_utc_offset().total_seconds())

def get_utc_offset():
    ts = time.time()
    return (dt.datetime.fromtimestamp(ts) - dt.datetime.utcfromtimestamp(ts))

def generate_hourly_stats(start_date,end_date,timestep=1):
    lo = string_to_datetime(start_date)
    hi = string_to_datetime(end_date)
    db = couchdb.Server('http://admin:password@115.146.93.197:5984/')['fin_tweets']
    lst = []
    while lo < hi:
        step = lo + dt.timedelta(hours=timestep)
        # get tweets 
        rows = db.view('_design/docs/_view/by_time', 
            startkey=lo.strftime('%Y-%m-%d %H:%M:%S'),
            endkey=step.strftime('%Y-%m-%d %H:%M:%S')
        )
        # genererate stats and print
        d = generate_stats(rows)
        lst.append((lo,step,d))
        # move lo up to step
        lo = step
    return lst

def generate_stats(rows):
    stats = {
        'eurusd':{'mentions':0, 'bullish':0, 'bearish':0},
        'audusd':{'mentions':0, 'bullish':0, 'bearish':0},
        'usdjpy':{'mentions':0, 'bullish':0, 'bearish':0},
        'usdcad':{'mentions':0, 'bullish':0, 'bearish':0},
        'gbpusd':{'mentions':0, 'bullish':0, 'bearish':0},
        'usdchf':{'mentions':0, 'bullish':0, 'bearish':0},
    }
    for row in rows:
        doc = row['value']
        # print row.key, doc['created_at']
        t_text = doc['text'].encode('ascii','ignore').lower()
        for key in stats:
            if key in t_text:
                stats[key]['mentions'] += 1
                if 'bull' in t_text:
                    stats[key]['bullish'] += 1
                elif 'bear' in t_text:
                    stats[key]['bearish'] += 1
    return stats

def string_to_datetime(str_date):
    '''
    str_date must have form yyyy-mm-dd hh:mm:dd
    '''
    tok = re.split(' |-|:',str_date)
    # convert to int
    for i, val in enumerate(tok):
        tok[i] = int(val)

    return dt.datetime(
        tok[0],tok[1],tok[2],tok[3],tok[4],tok[5]
    )

if __name__ == '__main__':
    main()
