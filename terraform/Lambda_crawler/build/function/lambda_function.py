# -*- config:utf-8 -*-
# Reference:
#   https://github.com/oreilly-japan/black-hat-python-2e-ja
#   __author__ = 'Hiroyuki Kakara'

import os, re, sys, json
import boto3
import hashlib
import requests
from pytz import timezone
from datetime import datetime, timedelta

import get_from_web

os.chdir(os.path.dirname(os.path.abspath(__file__)))

JOB_QUEUE = os.environ['JOB_QUEUE']
JOB_DEFINITION = os.environ['JOB_DEFINITION']
TWITTER_BEARER_TOKEN = os.environ['TWITTER_TOKEN']

BASE_TWITTER_URL = 'https://api.twitter.com/2'
HEADERS = {'Authorization': f'Bearer {TWITTER_BEARER_TOKEN}'}

RETURN_LIST_HASH = []


def create_id(hashs):
    return hashlib.md5("".join(sorted(set(hashs))).encode("utf-8")).hexdigest()


def get_tweets(user_id, interval):
    start_time = (datetime.now(timezone('UTC')) - \
        timedelta(minutes=interval)).strftime('%Y-%m-%dT%H:%M:%SZ')
    tweets = list()
    api_url  = f'{BASE_TWITTER_URL}/users/{user_id}/tweets'
    params  = {'start_time':  start_time, 'max_results': 100}

    while True:
        response = requests.get(api_url,params=params,headers=HEADERS)
        if response.status_code == 200:
            tweets.extend(response.json()['data'])
            if 'next_token' in response.json()['meta']:
                params['pagination_token'] = \
                    response.json()['meta']['next_token']
            else:
                return tweets
        else:
            return tweets


def extract_hash(tweet):
    hashes = list()
    pattern = re.compile(r'\b[0-9a-fA-F]{40}\b')
    result = re.findall(pattern, str(tweet))
    for sha1 in result:
        if sha1 not in hashes:
            hashes.append(sha1)

    pattern = re.compile(r'\b[0-9a-fA-F]{64}\b')
    result = re.findall(pattern, str(tweet))
    for sha256 in result:
        if sha256 not in hashes:
            hashes.append(sha256)

    pattern = re.compile(r'\b[0-9a-fA-F]{32}\b')
    result = re.findall(pattern, str(tweet))
    for md5 in result:
        if md5 not in hashes:
            hashes.append(md5)

    return hashes


def convert_screenname_userid(username):
    api_url  = f'{BASE_TWITTER_URL}/users/by/username/{username}'
    response = requests.get(api_url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()['data']['id']
    else:
        False


def extract_url( tweet ):
    pattern = re.compile(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+')
    result = re.findall(pattern, tweet)

    return result


def extract_hash_from_url(url):
    web = get_from_web.get_from_web()
    web_text =  web.get_web_content(url)
    if web_text == None:
        return []
    else:
        hashes = extract_hash(web_text)
        return hashes


def lambda_handler(event, context):
    interval = int(360) # 360 minuts = 6 hours
    print("[+] {0}: start".format(datetime.now()))

    usernames = open('accountlist.txt', 'r').readlines()
    for username in usernames:
        username = username.replace('\r', '').replace('\n', '')
        try:
            user_id = convert_screenname_userid(username)
            print("[+] {0}: username : {1}".format(datetime.now(), username))

            if user_id:
                try:
                    tweets = get_tweets(user_id, interval)
                except Exception as e:
                    print("[!] {0}: get_tweets Exception: {1}".format(datetime.now(), e))
                    continue

                for tweet in tweets:
                    hashes = extract_hash(tweet['text'])
                    urls = extract_url(tweet['text'])
                    for url in urls:
                        resolved_url = requests.get(url).url
                        hashes.extend(extract_hash(resolved_url))
                    if len(hashes) > 0:
                        print("[+] {0}: get hash {1}".format(datetime.now(), hashes))
                        RETURN_LIST_HASH.extend(hashes)
        except Exception as e:
            print("[!] {0}: tweets Exception: {1}".format(datetime.now(), e))

    usernames_article = open('accountlist_article.txt', 'r').readlines()
    for username_article in usernames_article:
        username = username_article.replace('\r', '').replace('\n', '')
        user_id = convert_screenname_userid(username)

        print("[+] {0}: username : {1}".format(datetime.now(), username))

        if user_id:
            try:
                tweets = get_tweets(user_id, interval)
            except Exception as e:
                print("[!] {0}: tweets Exception: {1}".format(datetime.now(), e))
                continue

            for tweet in tweets:
                hashes = extract_hash(tweet['text'])
                urls = extract_url(tweet['text'])
                for url in urls:
                    resolved_url = requests.get(url).url
                    print("[+] {0}: url : {1}".format(datetime.now(), resolved_url))
                    hashes.extend(extract_hash(resolved_url))

                    # web crawler
                    if resolved_url.startswith("https://twitter.com/"):
                        print("[+] {0}: skip crawle : {1}".format(datetime.now(), resolved_url))
                    else:
                        hashes.extend(extract_hash_from_url(resolved_url))

                if len(hashes)>0:
                    print("[+] {0}: get hash {1}".format(datetime.now(), hashes))
                    RETURN_LIST_HASH.extend(hashes)

    if RETURN_LIST_HASH:
        id = create_id(RETURN_LIST_HASH)
        print("[+] {0}: id {1}".format(datetime.now(), id))
        RETURN_LIST_HASH.insert(0, "/tmp/run.sh")
    else:
        print("[+] {0}: no hit".format(datetime.now()))
        return

    print("[+] {0}: commands {1}".format(datetime.now(), RETURN_LIST_HASH))

    client = boto3.client('batch')

    response = client.submit_job(
        jobName = "AnalysisJob_" + id,
        jobQueue = JOB_QUEUE,
        jobDefinition = JOB_DEFINITION,
        containerOverrides={
            'command': RETURN_LIST_HASH
            }
        )
    print(response)

    return {
        'statusCode':200,
        'headers':{
            'Content-Type': 'text/html',
        },
        'body': "http://" + os.environ['S3_BUCKET'] + "/" + id + "/index.html"
    }
