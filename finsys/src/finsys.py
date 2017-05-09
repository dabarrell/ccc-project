
import couchdb
import sys, os
import datetime as dt
import time

def main():
    db = couchdb.Server('http://admin:password@115.146.93.197:5984/')['fin_tweets']

    stats = {
        'eurusd':{'mentions':0, 'buys':0, 'sells':0},
        'audusd':{'mentions':0, 'buys':0, 'sells':0},
        'usdjpy':{'mentions':0, 'buys':0, 'sells':0},
        'usdcad':{'mentions':0, 'buys':0, 'sells':0},
        'gbpusd':{'mentions':0, 'buys':0, 'sells':0},
        'usdchf':{'mentions':0, 'buys':0, 'sells':0},
    }

    for row in db.view('_design/docs/_view/by_time', startkey='2017-05-05 13:00:00', endkey='2017-05-05 13:05:00'):
        doc = row['value']
        print row.key #, doc['created_at']
        t_text = doc['text'].encode('ascii','ignore').lower()
        for key in stats:
            if key in t_text:
                stats[key]['mentions'] += 1
                if 'buy' in t_text or 'long' in t_text:
                    stats[key]['buys'] += 1
                elif 'sell' in t_text or 'short' in t_text:
                    stats[key]['sells'] += 1
    
    for key, val in stats.iteritems():
        print key, val


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


if __name__ == '__main__':
    main()