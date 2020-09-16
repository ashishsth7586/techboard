# -*- coding: utf-8 -*-
import re

from scrapy import Request

from avc.items import AlexaItemLoader
from avc.spiders import BaseSpider


class AlexaComSpider(BaseSpider):
    name = 'alexa_com'

    def parse(self, response):
        self.logger.info("Input = %s", response.text)

        for entry in response.text.splitlines():
            url = entry
            if not re.search(r'^https?://www\.alexa\.com/siteinfo', url):
                url = 'http://www.alexa.com/siteinfo/{}'.format(url)
            yield Request(
                url,
                meta={'input_url': entry},
                callback=self.parse_item,
            )

    def parse_item(self, response):
        ail = AlexaItemLoader(response=response)
        ail.add_value('url', response.url)
        ail.add_value('website', response.url, re=r'/([^/]+)$')
        ail.add_css('global_rank', ".globleRank strong.metrics-data::text", re=r'[0-9,]+')
        ail.add_css(
            'daily_time',
            "*[data-cat=time_on_site] strong.metrics-data::text",
            re=r'\d{1,2}:\d{1,2}',
        )
        ail.add_css(
            'daily_pageviews',
            "*[data-cat=pageviews_per_visitor] strong.metrics-data::text",
            re=r'[0-9.]+',
        )
        ail.add_value('input_url', response.meta.get('input_url'))
        return ail.load_item()
