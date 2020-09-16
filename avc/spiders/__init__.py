import os

from datetime import datetime, timedelta

from hubstorage import HubstorageClient
from scrapy import Request, Spider


class BaseSpider(Spider):
    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        if 'crawl_days' in kwargs:
            self.crawl_type = 'full'
            self.crawl_days = int(self.crawl_days)
            assert self.crawl_days
        elif 'crawl_days' not in kwargs and 'crawl_type' not in kwargs:
            self.crawl_type = 'full'
            self.crawl_days = 14

    def start_requests(self):
        yield Request(self.input_url, callback=self.parse)

    def initialize_hubstorage_collection(self):
        self.hs_client = HubstorageClient(self.settings.get('HS_AUTH'))
        self.hs_projectid = os.environ.get('SCRAPY_PROJECT_ID')
        if self.hs_projectid is None:
            self.hs_projectid = self.settings.get('HS_PROJECTID')
        collections = self.hs_client.get_project(self.hs_projectid).collections
        self.hs_collection = collections.new_store(self.name)

    def set_min_post_date(self):
        if getattr(self, 'crawl_days', None):
            self.min_post_date = datetime.now() - timedelta(days=self.crawl_days)
        else:
            self.min_post_date = datetime.strptime(
                self.settings['AVC_MIN_POST_DATE'],
                self.settings['AVC_DATE_FORMAT'],
            )
        self.logger.info('Setting min_post_date as %s' % self.min_post_date)

    def get_latest_scraped_date(self, username):
        try:
            entry = self.hs_collection.get(username)
            return datetime.strptime(entry['value'], self.settings['AVC_DATE_TIME_FORMAT'])
        except:
            return None

    def set_latest_scraped_date(self, username, latest_scraped_date):
        entry = {
            '_key': username,
            'value': latest_scraped_date.strftime(self.settings['AVC_DATE_TIME_FORMAT']),
        }
        self.hs_collection.set(entry)
