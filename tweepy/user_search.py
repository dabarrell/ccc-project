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
tweetdb = couchdb.Server(server)['tweets']
testdb = couchdb.Server(server)['test']
userdb = couchdb.Server(server)['users']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

def rate_limit_handled(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError:
            print('Rate limit hit - sleeping 15 minutes')
            time.sleep(15*60)

while True:
    for id in tweetdb:
        try:
            username = tweetdb[id]['user']['screen_name']
            user_searched = False

            for user in userdb:
                if user == username:
                    user_searched = True
                    print('@{0} already searched'.format(username))
                    break

            if not user_searched:
                # grab all tweets from the user's history
                count = 0
                for status in rate_limit_handled(tweepy.Cursor(api.user_timeline, id = username).items(1000)):
                    doc = {'_id': status._json['id_str']}
                    doc.update(status._json)
                    testdb.save(doc)
                    count += 1
                    if debug is True:
                        print(doc)
                print('{0} tweets added for user @{1}'.format(count, username))

                # keep track of searched users
                user = {'_id':username}
                userdb.save(user)

        except couchdb.http.ResourceConflict:
            # duplicates in search & stream is expected, move on
            pass

        except Exception as e:
            print(e)
