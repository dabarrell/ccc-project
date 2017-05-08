import tweepy
import json

# Authentication details. To  obtain these visit dev.twitter.com
consumer_key = ''
consumer_secret = ''
access_token = ''
access_token_secret = ''

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# stuff = api.user_timeline(screen_name = 'goat_vegan', count = 100, include_rts = True)
stuff = api.search(q='python')

for status in stuff:
	# tweet = json.dumps(status._json,indent=4)
	print(status._json['text'] + '\n')

print(api.rate_limit_status())