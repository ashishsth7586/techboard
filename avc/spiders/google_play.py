# encoding: utf8

from avc.spiders.app_review_stats import AppReviewStatsSpider
from avc.items import AppReviewStatsItem


class GooglePlay(AppReviewStatsSpider):
    """Redmine ticket: https://intranet.scrapinghub.com/issues/84248"""
    name = 'google_play'
    custom_settings = {
        'DOWNLOADER_MIDDLEWARES': {
            'toolbox.mware.charityengine.CharityEngineMiddleware': 610,
            'toolbox.mware.charityengine.CharityEngineRedirectMiddleware': 600,
            'scrapy.downloadermiddleware.redirect.RedirectMiddleware': None,
            'toolbox.mware.charityengine.CharityEngineUserAgentMiddleware': 100,
            'toolbox.mware.proxystats.OpentsdbDownloaderStats': 851,
        },
        # you don't need this if your spider inherits from toolbox.spiders.base.Spider
        'DOWNLOAD_HANDLERS': {
            'https': 'toolbox.downloaderhandlers.http11.HTTP11DownloadHandler',
        },
    }

    def parse_app(self, response):
        item = AppReviewStatsItem()
        item['url'] = response.url
        item['name'] = response.css('div.id-app-title::text').extract_first()
        item['platform'] = 'Google Play'
        item['review_score'] = response.css('meta[itemprop=ratingValue]::attr(content)').extract_first()
        item['reviews_count'] = response.css('meta[itemprop=ratingCount]::attr(content)').extract_first()
        yield item
