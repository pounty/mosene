import tweepy
import praw
import requests
import os
import couchdb
import jsonpickle

from shutil import copyfile
from datetime import datetime, date, time, timedelta
from tweepy import Cursor

# details
consumer_key=""
consumer_secret=""

access_token=""
access_token_secret=""

# app-auth-couchdb

user = ""
password = ""
couchserver = couchdb.Server("http://%s:%s@localhost:5984/" % (user, password))
dbname = ""

if dbname in couchserver:
    db = couchserver[dbname]
else:
    db = couchserver.create(dbname)

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
    for status in Cursor(api.user_timeline, id=username, exclude_replies=True).items():
        if status.created_at < getbetweeninterval(interval):
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
    tweets = checkfornewtweet(user, 5)
    if len(tweets) != 0:
        for tweet in tweets:
            api.retweet(tweet.id)
            doc_id, doc_rev = db.save({'type': 'Tweet', 'name': jsonpickle.encode(tweet)})
        tweets.clear()

# main-app-reddit

def tweet_image(url, message):
    filename = 'temp.jpg'

    if url == "noimage":
        api.update_status(message)
    else:
        request = requests.get(url, stream=True)
        if request.status_code == 200:
         with open(filename, 'wb') as image:
            for chunk in request:
                image.write(chunk)

        if len(message) > 280:
            api.update_with_media(filename, status=message[:280])
        else:
            api.update_with_media(filename, status=message)
        os.remove(filename)

subs2watch = list()

subs2watch.append("movies")
subs2watch.append("television")

exists = os.path.isfile('./topposts_sent.tmp')

if exists:
    copyfile("topposts.tmp", "topposts_sent.tmp")

try:
    os.remove("topposts.tmp")
except:
    print("File not found")

for sub in subs2watch:
    for submission in reddit.subreddit(sub).hot(limit=5):
        thread_created = datetime.utcfromtimestamp(submission.created_utc)

        topposts_file = "topposts.tmp"
        twitter_file = "topposts_sent.tmp"

        open(topposts_file, "a").close()
        open(twitter_file, "a").close()

        open(topposts_file, "a+").write(submission.id + "\n")

        if submission.id not in open(twitter_file, "r").read():
            try:
                image = submission.preview.get("images")[0].get("source").get("url")
            except:
                image = "noimage"

            if len(submission.title) < 280:
                title = submission.title[:200]
            else:
                title = submission.title

            if "https://i.redd.it" in submission.url:
                text = title + " https://reddit.com" + submission.permalink
            else:
                text = title + " " + submission.url

            tweet_image(image, text)
            doc_id, doc_rev = db.save({'type': 'Reddit', 'name': jsonpickle.encode(submission)})
            open(twitter_file, "a+").write(submission.id + "\n")
