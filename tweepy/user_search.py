import tweepy
import json
import time
import couchdb

# Twitter API authentication details.
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

# CouchDB authentication details.
tweetdb = couchdb.Server('')['']
userdb = couchdb.Server('')['']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

def rate_limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            time.sleep(15*60)

while True:
    for id in tweetdb:
        try:
            username = tweetdb[id]['user']['screen_name']
            user_searched = False

            for user in userdb:
                if user == username:
                    user_searched = True
                    break

            if not user_searched:
                # grab all tweets from the user's history
                for status in rate_limit_handled(tweepy.Cursor(api.user_timeline, id = username).items(100)):
                    doc = {'_id': status._json['id_str']}
                    doc.update(status._json)
                    tweetdb.save(doc)

                # keep track of searched users
                user = {'_id':username}
                userdb.save(user)

        except couchdb.http.ResourceConflict:
            # duplicates in search & stream is expected, move on
            pass

        except Exception as e:
            print(e)
