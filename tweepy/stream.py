import tweepy
import json
import couchdb
import time

# Authentication details. To  obtain these visit dev.twitter.com
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''
tweetdb = couchdb.Server('http://user:user_pw@ip:5984/')['db_name']

# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):
    def on_data(self, data):
        # Twitter returns data in JSON format - we need to decode it first
        decoded = json.loads(data)
        # Also, we convert UTF-8 to ASCII ignoring all bad characters sent by users
        # print '@%s: %s' % (decoded['user']['screen_name'], decoded['text'].encode('ascii', 'ignore'))
        # print json.dumps(decoded['user']['screen_name'], indent=4)
        # print json.dumps(decoded,indent=4)
        try:
            doc = {
                '_id':decoded['id_str'],
                'text':decoded['text'],
                'coordinates':decoded['coordinates'],
                'user_name':decoded['user']['screen_name']
            }
            if decoded['place'] is not None:
                doc['place'] = decoded['place']['name']
            else:
                doc['place'] = None
            print doc
            print tweetdb.save(doc)
            print ''
        except Exception as e:
            print e
            # print json.dumps(decoded,indent=4)
            print '' 
        return True

    def on_error(self, status):
        print status

if __name__ == '__main__':
    '''
    110.95,-54.83,159.29,-11.35 # aus coords
    144.5937,-38.59,145.5125,-37.5113 # melbourne coords
    http://stackoverflow.com/questions/22889122/how-to-add-a-location-filter-to-tweepy-module
    http://boundingbox.klokantech.com/
    https://dev.twitter.com/streaming/overview/request-parameters#locations
    http://stackoverflow.com/questions/35268154/get-location-specific-tweets-from-twitter-using-tweepy?noredirect=1&lq=1
    '''
    l = StdOutListener()
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    key_word = 'australia'
    print "Showing all new tweets for " + key_word

    while True:
        try:
            # There are different kinds of streams: public stream, user stream, multi-user streams
            # In this example follow #programming tag
            # For more details refer to https://dev.twitter.com/docs/streaming-apis
            stream = tweepy.Stream(auth, l)
            # stream.filter(track=[key_word,'melbourne'])
            stream.filter(locations=[110.95,-54.83,159.29,-11.35],track=['melbourne'])
        except:
            print 'sleeping for 15 mins'
            print ''
            time.sleep(60*15)
            continue
