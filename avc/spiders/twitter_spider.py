import re

from datetime import datetime
from time import sleep

import twitter

from TwitterSearch import TwitterSearch, TwitterUserOrder

from avc.items import TwitterPageStatsItemLoader, TwitterPostDetailsItemLoader
from avc.spiders import BaseSpider


class TwitterBaseSpider(BaseSpider):
    request_delay = 60

    def __init__(self, *args, **kwargs):
        super(TwitterBaseSpider, self).__init__(*args, **kwargs)
        self.twitter_client = None

    def initialize_twitter_client(self):
        self.twitter_client = TwitterSearch(
            consumer_key=self.settings['TWITTER_CONSUMER_KEY'],
            consumer_secret=self.settings['TWITTER_CONSUMER_SECRET'],
            access_token=self.settings['TWITTER_ACCESS_TOKEN'],
            access_token_secret=self.settings['TWITTER_ACCESS_SECRET'],
        )

    def create_profile_url(self, username):
        return 'https://twitter.com/%s' % username

    def create_tweet_url(self, username, tweet_id):
        return 'https://twitter.com/%s/status/%s' % (username, tweet_id)

    def extract_username(self, text):
        if text.startswith('http://') or text.startswith('https://'):
            username = re.sub(r'^https?://twitter\.com/', '', text).strip('/')
        else:
            username = text

        if username.startswith('@'):
            username = username.replace('@', '', 1)

        return username


class TwitterPageStatsSpider(TwitterBaseSpider):
    name = 'twitter_page_stats'

    def parse(self, response):
        self.logger.info("Input file = %(input)s", {'input': response.text})
        client = twitter.Api(
            consumer_key=self.settings['TWITTER_CONSUMER_KEY'],
            consumer_secret=self.settings['TWITTER_CONSUMER_SECRET'],
            access_token_key=self.settings['TWITTER_ACCESS_TOKEN'],
            access_token_secret=self.settings['TWITTER_ACCESS_SECRET'],
        )
        users = [self.extract_username(s) for s in response.text.splitlines()]
        n_of_users = len(users)
        n_of_queries = 0

        for i, username in enumerate(users):
            index = i + 1
            try:
                if n_of_queries > 0 and n_of_queries % 5 == 0:
                    sleep(self.request_delay)
                self.logger.info(
                    "Processing user %(index)d/%(n_of_users)d %(username)s",
                    {'index': index, 'n_of_users': n_of_users, 'username': username},
                )
                n_of_queries += 1
                user = client.GetUser(screen_name=username)

                tpsil = TwitterPageStatsItemLoader()
                tpsil.add_value('username', username)
                tpsil.add_value('url', self.create_profile_url(username))
                tpsil.add_value('followers', str(user.followers_count))
                yield tpsil.load_item()
            except Exception as e:
                self.logger.exception(
                    "Error when requesting user %(index)d/%(n_of_users)d %(username)s",
                    {'index': index, 'n_of_users': n_of_users, 'username': username},
                )


class TwitterPostDetailsSpider(TwitterBaseSpider):
    name = 'twitter_post_details'

    def parse(self, response):
        self.logger.info("Input file = %(input)s", {'input': response.text})
        self.initialize_hubstorage_collection()
        self.set_min_post_date()
        self.initialize_twitter_client()
        users = [self.extract_username(s) for s in response.text.splitlines()]
        n_of_users = len(users)
        n_of_queries = 0

        for i, username in enumerate(users):
            index = i + 1
            self.logger.info(
                "Processing user %(index)d/%(n_of_users)d %(username)s",
                {'index': index, 'n_of_users': n_of_users, 'username': username},
            )

            latest_scraped_date = self.get_latest_scraped_date(username)
            if latest_scraped_date is None:
                latest_scraped_date = self.min_post_date
                self.logger.info(
                    "Get latest scraped date for %(index)d/%(n_of_users)d %(username)s "
                    "from default setting = %(date)s",
                    {
                        'index': index,
                        'n_of_users': n_of_users,
                        'username': username,
                        'date': latest_scraped_date,
                    },
                )
            else:
                self.logger.info(
                    "Get latest scraped date for %(index)d/%(n_of_users)d %(username)s "
                    "from collection = %(date)s",
                    {
                        'index': index,
                        'n_of_users': n_of_users,
                        'username': username,
                        'date': latest_scraped_date,
                    },
                )

            new_latest_scraped_date = latest_scraped_date
            next_max_id = None
            scraped_tweets_counter = 0

            while True:
                if n_of_queries > 0 and n_of_queries % 5 == 0:
                    self.logger.info(
                        "Sleep for %(delay)s seconds to avoid rate limit. Queries = %(queries)s",
                        {'delay': self.request_delay, 'queries': n_of_queries}
                    )
                    sleep(self.request_delay)

                tuo = TwitterUserOrder(username)
                if next_max_id is None:
                    # bug on TwitterSearch since arguments is a class (not object) instance
                    # so it "remembers" previous user max_id
                    if 'max_id' in tuo.arguments:
                        del tuo.arguments['max_id']
                    self.logger.info(
                        "Initial request for %(index)d/%(n_of_users)d %(username)s",
                        {'index': index, 'n_of_users': n_of_users, 'username': username},
                    )
                else:
                    tuo.set_max_id(next_max_id)
                    self.logger.info(
                        "Next request for %(index)d/%(n_of_users)d %(username)s, max ID = %(id)s",
                        {
                            'index': index,
                            'n_of_users': n_of_users,
                            'username': username,
                            'id': next_max_id,
                        },
                    )

                n_of_queries += 1

                try:
                    twitter_response = self.twitter_client.search_tweets(tuo)
                except:
                    self.logger.exception(
                        "Finished requesting tweets for user %(index)d/%(n_of_users)d %(username)s"
                        " because there is exception",
                        {'index': index, 'n_of_users': n_of_users, 'username': username},
                    )
                    break

                tweet_available = len(twitter_response['content']) > 0
                if not tweet_available:
                    self.logger.info(
                        "Finished requesting tweets for user %(index)d/%(n_of_users)d %(username)s"
                        " because there is no more tweet",
                        {'index': index, 'n_of_users': n_of_users, 'username': username},
                    )
                    break

                next_max_id = min([t['id'] for t in twitter_response['content']]) - 1
                self.logger.info(
                    "Next max ID = %(id)s for %(index)d/%(n_of_users)d %(username)s",
                    {
                        'id': next_max_id,
                        'index': index,
                        'n_of_users': n_of_users,
                        'username': username,
                    },
                )
                profile_url = self.create_profile_url(username)
                any_skipped_tweet = False

                for tweet in twitter_response['content']:
                    tweet_created_at = datetime.strptime(
                        tweet['created_at'],
                        '%a %b %d %H:%M:%S +0000 %Y',
                    )

                    if self.crawl_type == 'incremental':
                        if tweet_created_at <= latest_scraped_date:
                            any_skipped_tweet = True
                            self.logger.info(
                                "Not scraping tweet: %(tweet_id)s because tweet['created_at'] "
                                "(%(created_at)s) <= latest scraped date (%(latest_scraped_date)s)"
                                " for %(username)s and crawl type is incremental",
                                {
                                    'tweet_id': tweet['id'],
                                    'created_at': tweet_created_at,
                                    'latest_scraped_date': latest_scraped_date,
                                    'username': username,
                                },
                            )
                            continue
                    else:
                        if tweet_created_at <= self.min_post_date:
                            any_skipped_tweet = True
                            self.logger.info(
                                "Not scraping tweet: %(tweet_id)s because tweet['created_at'] "
                                "(%(created_at)s) <= min post date (%(min_post_date)s)"
                                " for %(username)s and crawl type is full",
                                {
                                    'tweet_id': tweet['id'],
                                    'created_at': tweet_created_at,
                                    'min_post_date': self.min_post_date,
                                    'username': username,
                                },
                            )
                            continue

                    if 'retweeted_status' in tweet:
                        self.logger.debug(
                            "Skip retweet for %(username)s %(id)s",
                            {'username': username, 'id': tweet['id']}
                        )
                        continue

                    if tweet_created_at > new_latest_scraped_date:
                        new_latest_scraped_date = tweet_created_at

                    tpdil = TwitterPostDetailsItemLoader()
                    tpdil.add_value('username', username)
                    tpdil.add_value('url', profile_url)
                    tpdil.add_value('followers', str(tweet['user']['followers_count']))
                    tpdil.add_value('tweet_url', self.create_tweet_url(username, tweet['id']))
                    tpdil.add_value('likes', str(tweet['favorite_count']))
                    tpdil.add_value('retweets', str(tweet['retweet_count']))
                    yield tpdil.load_item()
                    self.logger.info(
                        "Scraped tweet ID %(tweet_id)s, created at %(date)s for %(username)s",
                        {'tweet_id': tweet['id'], 'date': tweet_created_at, 'username': username},
                    )
                    scraped_tweets_counter += 1

                if any_skipped_tweet:
                    self.logger.info(
                        "Finished requesting tweets for user %(index)d/%(n_of_users)d %(username)s"
                        " because there is skipped tweet",
                        {'index': index, 'n_of_users': n_of_users, 'username': username},
                    )
                    break

            self.logger.info(
                "Scraped %(counter)d tweets for user %(index)d/%(n_of_users)d %(username)s",
                {
                    'counter': scraped_tweets_counter,
                    'index': index,
                    'n_of_users': n_of_users,
                    'username': username,
                },
            )

            if new_latest_scraped_date > latest_scraped_date:
                self.logger.info(
                    "Store new latest scraped date for %(index)d/%(n_of_users)d %(username)s "
                    "= %(date)s",
                    {
                        'index': index,
                        'n_of_users': n_of_users,
                        'username': username,
                        'date': new_latest_scraped_date,
                    },
                )
                self.set_latest_scraped_date(username, new_latest_scraped_date)
