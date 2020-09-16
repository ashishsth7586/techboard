# encoding: utf8

from avc.spiders.app_review_stats import AppReviewStatsSpider
from avc.items import AppReviewStatsItemLoader


class Itunes(AppReviewStatsSpider):
    """Redmine ticket: https://intranet.scrapinghub.com/issues/84250"""
    name = 'itunes'
    custom_settings = {
    }

    def parse_app(self, response):
        loader = AppReviewStatsItemLoader(response=response)
        loader.add_value('url', response.url)
        loader.add_value('platform', 'Itunes')
        loader.add_css('name', 'h1::text')
        loader.add_css(
            'review_score',
            'script[type="application/ld+json"]::text',
            re='"ratingValue":([0-9.]+)'
        )
        loader.add_css(
            'reviews_count',
            'script[type="application/ld+json"]::text',
            re='"reviewCount":([0-9]+)'
        )
        yield loader.load_item()
