import json

import dateparser

from scrapy import Request

from avc.items import LinkedinPageStatsItemLoader, LinkedinPostDetailsItemLoader
from avc.spiders import BaseSpider


class LinkedinBaseSpider(BaseSpider):
    custom_settings = {
        'USER_AGENT': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36'
        ),
        'DOWNLOADER_MIDDLEWARES': {
            'toolbox.mware.charityengine.CharityEngineMiddleware': 610,
            'toolbox.mware.charityengine.CharityEngineRedirectMiddleware': 600,
            'scrapy.downloadermiddleware.redirect.RedirectMiddleware': None,
            'toolbox.mware.charityengine.CharityEngineUserAgentMiddleware': 100,
            'toolbox.mware.proxystats.OpentsdbDownloaderStats': 851,
        },
        'DOWNLOAD_HANDLERS': {
            'http': 'toolbox.downloaderhandlers.http11.HTTP11DownloadHandler',
            'https': 'toolbox.downloaderhandlers.http11.HTTP11DownloadHandler',
        },
    }

    company_url = 'https://www.linkedin.com/company/{company}'

    def parse(self, response):
        for company in response.body.splitlines():
            url = company
            if 'linkedin.com' not in url:
                url = self.company_url.format(company=company)
            yield Request(
                url,
                meta={'company': company},
                callback=self.parse_company,
            )

    def get_json_data(self, response):
        code = response.xpath(
            "//*[@id='stream-promo-top-bar-embed-id-content']/comment()"
        ).re(r'^<!--(.+)-->$')
        if len(code) == 0:
            self.logger.error(
                "Can't find stream-promo-top-bar-embed-id-content on %(url)s",
                {'url': response.url},
            )
            return None

        return json.loads(code[0])


class LinkedinPageStatsSpider(LinkedinBaseSpider):
    #name = 'linkedin_page_stats'

    def parse_company(self, response):
        json_data = self.get_json_data(response)
        lpsil = LinkedinPageStatsItemLoader()
        lpsil.add_value('url', response.url)
        lpsil.add_value('followers', str(json_data['followerCount']))
        return lpsil.load_item()


class LinkedinPostDetailsSpider(LinkedinBaseSpider):
    #name = 'linkedin_post_details'

    feed_url = 'https://www.linkedin.com/biz/{company_id}/feed?start={start}&v2=true'
    posts_per_page = 10

    def parse(self, response):
        self.initialize_hubstorage_collection()
        self.set_min_post_date()

        for req in super(LinkedinPostDetailsSpider, self).parse(response):
            yield req

    def parse_company(self, response):
        company = response.meta.get('company')
        json_data = self.get_json_data(response)
        return Request(
            self.feed_url.format(company_id=json_data['companyId'], start=0),
            headers={
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Referer': 'https://www.linkedin.com/',
                'X-Requested-With': 'XMLHttpRequest',
            },
            meta={
                'company': company,
                'company_url': response.url,
                'company_id': json_data['companyId'],
            },
            callback=self.parse_feed,
        )

    def parse_feed(self, response):
        company = response.meta.get('company')
        company_url = response.meta.get('company_url')

        latest_scraped_date = response.meta.get(
            'latest_scraped_date',
            self.get_latest_scraped_date(company),
        )
        if latest_scraped_date is None:
            latest_scraped_date = self.min_post_date
            self.logger.info(
                "Get latest scraped date for %(company)s from default setting = %(date)s",
                {'company': company, 'date': latest_scraped_date},
            )
        elif 'new_latest_scraped_date' not in response.meta:
            self.logger.info(
                "Get latest scraped date for %(company)s from collection = %(date)s",
                {'company': company, 'date': latest_scraped_date},
            )

        new_latest_scraped_date = response.meta.get('new_latest_scraped_date', latest_scraped_date)
        any_skipped_post = False
        posts = response.css("li.feed-item")

        for post in posts:
            post_created_time_text = post.css("a.nus-timestamp::text").extract_first()
            if post_created_time_text is None:
                self.logger.error(
                    "Can't find post created time on %(post)s %(url)s",
                    {'post': post.extract(), 'url': response.url}
                )
                continue
            post_created_time = dateparser.parse(post_created_time_text)

            if self.crawl_type == 'incremental':
                if post_created_time <= latest_scraped_date:
                    any_skipped_post = True
                    self.logger.info(
                        "Not scraping post: %(post)s because post['created_time'] "
                        "(%(created_time)s) <= latest scraped date (%(latest_scraped_date)s)"
                        " for %(company)s and crawl type is incremental",
                        {
                            'post': post.extract(),
                            'created_time': post_created_time,
                            'latest_scraped_date': latest_scraped_date,
                            'company': company,
                        },
                    )
                    continue
            else:
                if post_created_time <= self.min_post_date:
                    any_skipped_post = True
                    self.logger.info(
                        "Not scraping post: %(post)s because tweet['created_at'] "
                        "(%(created_at)s) <= min post date (%(min_post_date)s)"
                        " for %(company)s and crawl type is full",
                        {
                            'post': post.extract(),
                            'created_time': post_created_time,
                            'min_post_date': self.min_post_date,
                            'company': company,
                        },
                    )
                    continue

            if post_created_time > new_latest_scraped_date:
                new_latest_scraped_date = post_created_time

            lpdil = LinkedinPostDetailsItemLoader(selector=post)
            lpdil.add_value('url', company_url)
            lpdil.add_css('post_url', "a.nus-timestamp::attr(href)")
            lpdil.add_value(
                'post_date',
                post_created_time.strftime(self.settings['AVC_DATE_TIME_FORMAT']),
            )
            # lpdil.add_value('shares')
            lpdil.add_css('likes', "span.show-like > a.like::attr(data-li-num-liked)")
            lpdil.add_css('comments', "li.feed-comment > a::attr(data-li-num-commented)")
            yield lpdil.load_item()

        send_next_listing_request = False

        if len(posts) == 0:
            self.logger.info(
                "Finished requesting posts for page %(company)s because there is no more post",
                {'company': company},
            )
        elif any_skipped_post:
            self.logger.info(
                "Finished requesting posts for page %(company)s because there is skipped post",
                {'company': company},
            )
        else:
            send_next_listing_request = True
            start = response.meta.get('start', 0) + self.posts_per_page
            company_id = response.meta.get('company_id')
            self.logger.info(
                "Requesting next post listing for %(company)s on %(url)s",
                {'company': company, 'url': response.url},
            )
            yield Request(
                self.feed_url.format(company_id=company_id, start=start),
                meta={
                    'company': company,
                    'company_url': company_url,
                    'company_id': company_id,
                    'start': start,
                    'latest_scraped_date': latest_scraped_date,
                    'new_latest_scraped_date': new_latest_scraped_date,
                },
                callback=self.parse_feed,
            )

        if not send_next_listing_request and new_latest_scraped_date > latest_scraped_date:
            self.logger.info(
                "Store new latest scraped date for %(company)s = %(date)s",
                {'company': company, 'date': new_latest_scraped_date},
            )
            self.set_latest_scraped_date(company, new_latest_scraped_date)
