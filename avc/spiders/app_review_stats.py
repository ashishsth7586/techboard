# encoding: utf8

import scrapy


class AppReviewStatsSpider(scrapy.Spider):
    """
    Redmine tickets:
      - https://intranet.scrapinghub.com/issues/84248
      - https://intranet.scrapinghub.com/issues/84250
    """

    def start_requests(self):
        debug_url = getattr(self, 'debug_url', None)
        if debug_url:
            yield scrapy.Request(
                debug_url,
                callback=self.parse_app
            )
            return
        input_url = getattr(self, 'input_url', None)
        if input_url:
            yield scrapy.Request(
                input_url,
                meta={
                    'dont_proxy': True,
                    'dont_obey_robotstxt': True,
                },
                callback=self.parse
            )

    def parse(self, response):
        for line in response.body.splitlines():
            self.crawler.stats.inc_value('app_url/yielded')
            yield scrapy.Request(
                line,
                callback=self.parse_app
            )

    def parse_app(self, response):
        raise NotImplementedError
