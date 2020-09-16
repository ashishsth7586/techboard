# -*- coding: utf-8 -*-
from scrapy import Field, Item
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst


class AvcItem(Item):
    url = Field()
    crawl_time = Field()


class AvcItemLoader(ItemLoader):
    default_item_class = AvcItem
    default_input_processor = lambda context, values: filter(None, (y.strip() for y in values))
    default_output_processor = TakeFirst()


class AlexaItem(AvcItem):
    website = Field()
    global_rank = Field()
    daily_time = Field()
    daily_pageviews = Field()
    input_url = Field()


class AlexaItemLoader(AvcItemLoader):
    default_item_class = AlexaItem


class TwitterPageStatsItem(AvcItem):
    username = Field()
    followers = Field()


class TwitterPageStatsItemLoader(AvcItemLoader):
    default_item_class = TwitterPageStatsItem


class TwitterPostDetailsItem(AvcItem):
    username = Field()
    followers = Field()
    tweet_url = Field()
    likes = Field()
    retweets = Field()
    mention = Field()


class TwitterPostDetailsItemLoader(AvcItemLoader):
    default_item_class = TwitterPostDetailsItem


class FacebookPageStatsItem(AvcItem):
    page_likes = Field()


class FacebookPageStatsItemLoader(AvcItemLoader):
    default_item_class = FacebookPageStatsItem


class FacebookPostDetailsItem(AvcItem):
    post_id = Field()
    post_url = Field()
    post_date = Field()
    shared_count = Field()
    likes = Field()
    comments = Field()


class FacebookPostDetailsItemLoader(AvcItemLoader):
    default_item_class = FacebookPostDetailsItem


class LinkedinPageStatsItem(AvcItem):
    followers = Field()


class LinkedinPageStatsItemLoader(AvcItemLoader):
    default_item_class = LinkedinPageStatsItem


class LinkedinPostDetailsItem(AvcItem):
    post_url = Field()
    post_date = Field()
    likes = Field()
    shares = Field()
    comments = Field()


class LinkedinPostDetailsItemLoader(AvcItemLoader):
    default_item_class = LinkedinPostDetailsItem


class GoogleNewsItem(AvcItem):
    article_date = Field()
    first_paragraph = Field()
    headline = Field()
    keywords = Field()
    news_url = Field()
    position = Field()
    search_url = Field()
    website = Field()


class AppReviewStatsItem(AvcItem):
    name = Field()
    platform = Field()
    review_score = Field()
    reviews_count = Field()
    review_score_current = Field()
    reviews_count_current = Field()


class AppReviewStatsItemLoader(AvcItemLoader):
    default_item_class = AppReviewStatsItem
