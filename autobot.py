import tweepy
import praw
import requests
import os

from datetime import datetime, date, time, timedelta
from tweepy import Cursor

# details
consumer_key=""
consumer_secret=""

access_token=""
access_token_secret=""

# app-auth-twitter

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)

auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)

# app-auth-reddit

reddit = praw.Reddit(client_id='',
        client_secret='',
        user_agent='python:mosene:v1 (by /u/<>)')

# main-app-twitter

alltweets = list()

def getbetweeninterval(interval):
    return datetime.utcnow() - timedelta(minutes=interval)

def checkfornewtweet(username, interval):
    global alltweets
    for status in Cursor(api.user_timeline, id=username).items():
        if status.created_at < getbetweeninterval(interval):
            break
        elif hasattr(status, "in_reply_to_user_id"):
            break
        else:
            alltweets.append(status)
        
    return alltweets

users2watch = list()

users2watch.append("NXonNetflix")
users2watch.append("schnittbericht")
users2watch.append("boxofficemojo")
users2watch.append("BDisgusting")
users2watch.append("iTunes")
users2watch.append("empiremagazine")
users2watch.append("Collider")
users2watch.append("RottenTomatoes")
users2watch.append("BFI")
users2watch.append("PrimeVideoDE")

tweets = list()

for user in users2watch:
    print(user)
    tweets = checkfornewtweet(user, 5)
    if len(tweets) != 0:
        for tweet in tweets:
            api.retweet(tweet.id)
        tweets.clear()

# main-app-reddit

def tweet_image(url, message):
    filename = 'temp.jpg'
    request = requests.get(url, stream=True)
    if request.status_code == 200:
        with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        api.update_with_media(filename, status=message)
        os.remove(filename)

subs2watch = list()

subs2watch.append("movies")
subs2watch.append("television")

for sub in subs2watch:        
    for submission in reddit.subreddit(sub).hot(limit=10):
        thread_created = datetime.utcfromtimestamp(submission.created_utc)

        if thread_created < getbetweeninterval(5):
            continue
        else:
            image = submission.preview.get("images")[0].get("source").get("url")

        if "https://i.redd.it" in submission.url:
            text = submission.title + " https://reddit.com" + submission.permalink
        else:
            text = submission.title + " " + submission.url
        
        tweet_image(image, text)
