import json
import re

from datetime import datetime

from scrapy import Request

from avc.items import FacebookPageStatsItemLoader, FacebookPostDetailsItemLoader
from avc.spiders import BaseSpider


class FacebookBaseSpider(BaseSpider):
    api_url = 'https://graph.facebook.com/v2.6'

    def __init__(self, *args, **kwargs):
        super(FacebookBaseSpider, self).__init__(*args, **kwargs)
        self.access_token = None
        self.pages = []

    def parse(self, response):
        self.logger.info("Input = %s", response.text)

        for page in response.text.splitlines():
            page_slug = page
            page_slugs = re.findall(r'facebook\.com/([^/]+)', page)
            if page_slugs:
                page_slug = page_slugs[0]
            self.pages.append(page_slug)

        get_token_url = (
            '%s/oauth/access_token?client_id=%s&client_secret=%s&grant_type=client_credentials'
        )

        return Request(
            get_token_url % (
                self.api_url,
                self.settings['FACEBOOK_APP_ID'],
                self.settings['FACEBOOK_APP_SECRET'],
            ),
            callback=self.parse_access_token,
        )

    def parse_access_token(self, response):
        data = json.loads(response.body)
        self.access_token = data['access_token']

        for req in self.main_requests(response):
            yield req

    def main_requests(self, response):
        raise NotImplementedError

    def get_access_token(self):
        return '%s|%s' % (self.settings['FACEBOOK_APP_ID'], self.settings['FACEBOOK_APP_SECRET'])


class FacebookPageStatsSpider(FacebookBaseSpider):
    name = 'facebook_page_stats'

    page_url = (
        '%s/%s?fields=link,fan_count&access_token=%s'
    )

    def main_requests(self, response):
        for page in self.pages:
            yield Request(
                self.page_url % (self.api_url, page, self.access_token),
                meta={'page': page, 'handle_httpstatus_all': True},
                callback=self.parse_page,
            )

    def parse_page(self, response):
        page = response.meta.get('page')
        data = json.loads(response.body)

        if 'error' in data and data['error']['code'] == 803:
            page_ids = re.findall(r'\d{15,16}', page)
            for page_id in page_ids:
                self.logger.info(
                    "Requesting with page_id = %(page_id)s for %(page)s, %(url)s",
                    {'page_id': page_id, 'page': page, 'url': response.url},
                )
                yield Request(
                    self.page_url % (self.api_url, page_id, self.access_token),
                    meta={
                        'page': page,
                        'page_id': page_id,
                        'handle_httpstatus_all': True,
                    },
                    callback=self.parse_page,
                )
            return
        elif 'error' in data and data['error']['code'] == 100:
            self.logger.info(
                "Page %(page)s can't be accessed with app token, retry with user token = "
                "%(token)s",
                {'page': page, 'token': self.settings.get('FACEBOOK_USER_TOKEN')},
            )
            if response.meta.get('page_id'):
                page_id = response.meta['page_id']
                yield Request(
                    self.page_url % (
                        self.api_url,
                        page_id,
                        self.settings.get('FACEBOOK_USER_TOKEN'),
                    ),
                    meta={'page': page, 'page_id': page_id, 'handle_httpstatus_all': True},
                    callback=self.parse_page,
                )
            else:
                yield Request(
                    self.page_url % (self.api_url, page, self.settings.get('FACEBOOK_USER_TOKEN')),
                    meta={'page': page, 'handle_httpstatus_all': True},
                    callback=self.parse_page,
                )
            return
        elif 'error' in data:
            self.logger.error(
                "Can't get data for %(page)s, message: %(message)s",
                {'page': page, 'message': data['error']['message']},
            )
            return

        fan_count = data.get('fan_count')
        if fan_count is None and 'name' in data:
            name = re.sub(r'\s', '', data['name'])
            yield Request(
                self.page_url % (self.api_url, name, self.access_token),
                meta={'page': page, 'handle_httpstatus_all': True},
                callback=self.parse_page,
            )

        page_url = data.get('link')
        if page_url is None and 'name' in data:
            page_url = 'https://facebook/com/' + data['name']

        fpsil = FacebookPageStatsItemLoader()
        fpsil.add_value('url', page_url)
        fpsil.add_value('page_likes', str(fan_count))
        yield fpsil.load_item()


class FacebookPostDetailsSpider(FacebookBaseSpider):
    name = 'facebook_post_details'

    post_url = (
        '%s/%s/posts?fields=id,status_type,from{id,username,link},created_time,shares,'
        'likes.summary(true),comments.summary(true)'
        '&access_token=%s'
    )

    def main_requests(self, response):
        self.initialize_hubstorage_collection()
        self.set_min_post_date()

        for page in self.pages:
            yield Request(
                self.post_url % (self.api_url, page, self.access_token),
                meta={'page': page, 'handle_httpstatus_all': True},
                callback=self.parse_posts,
            )

    def parse_posts(self, response):
        data = json.loads(response.body)
        page = response.meta.get('page')

        if 'error' in data and data['error']['code'] == 803:
            page_ids = re.findall(r'\d{15,16}', page)
            for page_id in page_ids:
                self.logger.info(
                    "Requesting with page_id = %(page_id)s for %(page)s, %(url)s",
                    {'page_id': page_id, 'page': page, 'url': response.url},
                )
                yield Request(
                    self.post_url % (self.api_url, page_id, self.access_token),
                    meta={'page': page, 'handle_httpstatus_all': True},
                    callback=self.parse_posts,
                )
            return
        elif 'error' in data and data['error']['code'] == 100:
            self.logger.info(
                "Page %(page)s can't be accessed with app token, retry with user token = "
                "%(token)s",
                {'page': page, 'token': self.settings.get('FACEBOOK_USER_TOKEN')},
            )
            if response.meta.get('page_id'):
                page_id = response.meta['page_id']
                yield Request(
                    self.post_url % (
                        self.api_url,
                        page_id,
                        self.settings.get('FACEBOOK_USER_TOKEN'),
                    ),
                    meta={'page': page, 'page_id': page_id, 'handle_httpstatus_all': True},
                    callback=self.parse_posts,
                )
            else:
                yield Request(
                    self.post_url % (self.api_url, page, self.settings.get('FACEBOOK_USER_TOKEN')),
                    meta={'page': page, 'handle_httpstatus_all': True},
                    callback=self.parse_posts,
                )
            return

        if 'data' not in data:
            self.logger.error(
                "Can't find page %(page)s, response: %(data)s",
                {'page': page, 'data': data},
            )
            return

        latest_scraped_date = response.meta.get(
            'latest_scraped_date',
            self.get_latest_scraped_date(page),
        )
        if latest_scraped_date is None:
            latest_scraped_date = self.min_post_date
            self.logger.info(
                "Get latest scraped date for %(page)s from default setting = %(date)s",
                {'page': page, 'date': latest_scraped_date},
            )
        elif 'new_latest_scraped_date' not in response.meta:
            self.logger.info(
                "Get latest scraped date for %(page)s from collection = %(date)s",
                {'page': page, 'date': latest_scraped_date},
            )

        new_latest_scraped_date = response.meta.get('new_latest_scraped_date', latest_scraped_date)
        any_skipped_post = False

        for post in data['data']:
            post_created_time = datetime.strptime(post['created_time'][:19], '%Y-%m-%dT%H:%M:%S')
            if self.crawl_type == 'incremental':
                if post_created_time <= latest_scraped_date:
                    any_skipped_post = True
                    self.logger.info(
                        "Not scraping post: %(post_id)s because post['created_time'] "
                        "(%(created_time)s) <= latest scraped date (%(latest_scraped_date)s)"
                        " for %(page)s and crawl type is incremental",
                        {
                            'post_id': post['id'],
                            'created_time': post['created_time'],
                            'latest_scraped_date': latest_scraped_date,
                            'page': page,
                        },
                    )
                    continue
            else:
                if post_created_time <= self.min_post_date:
                    any_skipped_post = True
                    self.logger.info(
                        "Not scraping post: %(post_id)s because post['created_at'] "
                        "(%(created_time)s) <= min post date (%(min_post_date)s)"
                        " for %(page)s and crawl type is full",
                        {
                            'post_id': post['id'],
                            'created_time': post['created_time'],
                            'min_post_date': self.min_post_date,
                            'page': page,
                        },
                    )
                    continue

            if post_created_time > new_latest_scraped_date:
                new_latest_scraped_date = post_created_time

            post_id = post['id'].split('_')[1]
            fpdil = FacebookPostDetailsItemLoader()
            fpdil.add_value('url', post['from']['link'])
            fpdil.add_value('post_id', post_id)
            fpdil.add_value('post_url', '%sposts/%s' % (post['from']['link'], post_id))
            fpdil.add_value('post_date', post_created_time.strftime('%B %d, %Y at %H:%M'))
            fpdil.add_value('shared_count', str(post.get('shares', {}).get('count')))
            if post.get('likes', {}).get('summary', {}).get('total_count'):
                fpdil.add_value('likes', str(post['likes']['summary']['total_count']))
            if post.get('comments', {}).get('summary', {}).get('total_count'):
                fpdil.add_value('comments', str(post['comments']['summary']['total_count']))
            yield fpdil.load_item()

        send_next_listing_request = False

        if len(data['data']) == 0:
            self.logger.info(
                "Finished requesting posts for page %(page)s because there is no more post",
                {'page': page},
            )
        elif any_skipped_post:
            self.logger.info(
                "Finished requesting posts for page %(page)s because there is skipped post",
                {'page': page},
            )
        else:
            if 'next' in data['paging']:
                send_next_listing_request = True
                self.logger.info(
                    "Requesting next post listing for %(page)s on %(url)s",
                    {'page': page, 'url': response.url},
                )
                yield Request(
                    data['paging']['next'],
                    meta={
                        'page': page,
                        'latest_scraped_date': latest_scraped_date,
                        'new_latest_scraped_date': new_latest_scraped_date,
                    },
                    callback=self.parse_posts,
                )
            else:
                self.logger.info(
                    "Next post listing URL for page %(page)s is not available on %(url)s",
                    {'page': page, 'url': response.url}
                )

        if not send_next_listing_request and new_latest_scraped_date > latest_scraped_date:
            self.logger.info(
                "Store new latest scraped date for %(page)s = %(date)s",
                {'page': page, 'date': new_latest_scraped_date},
            )
            self.set_latest_scraped_date(page, new_latest_scraped_date)
