# coding: utf8
import codecs
from urllib.request import urlopen
import urllib.parse
import datetime
import scrapy
import dateparser

import avc.items
import csv 
import avc.db as db

class GoogleNewsSpider(scrapy.Spider):
    name = 'google_news'
    custom_settings = {
        'USER_AGENT': (
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Ubuntu Chromium/51.0.2704.79 Chrome/51.0.2704.79 Safari/537.36'
        ),
        'DOWNLOADER_MIDDLEWARES': {
            #'toolbox.mware.proxystats.OpentsdbDownloaderStats': 851,
            'scrapy_crawlera.CrawleraMiddleware': 610
        },
        # 'DOWNLOAD_HANDLERS': {
        #     'http': 'toolbox.downloaderhandlers.http11.HTTP11DownloadHandler',
        #     'https': 'toolbox.downloaderhandlers.http11.HTTP11DownloadHandler',
        # },
        'COOKIES_ENABLED': False,
        #'DUPEFILTER_CLASS': 'scrapy.dupefilters.BaseDupeFilter'
        
        
    }

   
    def __init__(
            self, max_urls=2, excluded_domains_urls=None, keywords_urls=None,
            crawl_days='30', *args, **kwargs
        ):

         
        """Initializes the instance"""
        super(GoogleNewsSpider, self).__init__(*args, **kwargs)
        def get_read_split(url):
            return [
                x.strip()
                for x in urllib.request.urlopen(url).read().replace(codecs.BOM_UTF8, '').splitlines()
                if x.strip()
            ]
        self.max_urls = int(max_urls)
        if excluded_domains_urls:
            tmp = get_read_split(excluded_domains_urls)
            tmp = [
                urllib.parse.urlparse(x).netloc if '://' in x else x
                for x in tmp
            ]
            tmp = [
                x[4:] if x.startswith('www.') else x
                for x in tmp
            ]
            self.excluded_domains = tmp

        else:
            self.excluded_domains = None
        if keywords_urls:
            self.keywords = get_read_split(keywords_urls)
        else:
            self.keywords = None
        if crawl_days == 'default':
            self.search_tbs = None
        elif crawl_days.isdigit():
            now = datetime.datetime.utcnow()
            timeframes = db.get_job_timeframes()
            for row in timeframes:
                start_time = row[0]
                end_time = row[1]
          
            self.search_tbs = 'cdr:1,cd_min:%s,cd_max:%s'% (start_time, end_time)
           
        else:
            self.search_tbs = 'cdr:1,%s' % crawl_days

    def start_requests(self):
        """Generates the initial requests"""
        for attr in ('max_urls', 'excluded_domains', 'keywords'):
            self.logger.info('Using %s=%s', attr, getattr(self, attr))
        
            merged_keywords=[]
            keywords = db.get_keywords()
            for row in keywords:
                companies = db.get_companies()
                for row_comp in companies:
                    word = row_comp[0]+','+row[0]
                    merged_keywords.append(word)

        merged_keywords = ['news']
        print(merged_keywords)

        self.keywords = merged_keywords
        for keyword in self.keywords:
            formdata = {
                'hl': 'en',
                'gl': 'au',
                'tbm': 'nws',
                'gws_rd': 'cr',
                'q': keyword,
                'tbs': self.search_tbs,
            }
            yield scrapy.FormRequest(
                url='https://www.google.com/search',
                method='GET',
                formdata=formdata,
                meta={
                    'keyword': keyword,
                    'dont_redirect': True,
                    'handle_httpstatus_list': [301,302]
                },
                dont_filter=True,
                callback=self.parse_search_results
            )

    def parse_search_results(self, response):
        """Parses a search result response"""        
        results = response.css('div#search div.dbsr')
        if len(results) and not response.css('div[data-async-context]'):
            try_number = response.meta.get('_retry_times', 0)
            self.logger.error('Non-JS response on %s, try %d', response.url, try_number)
            if try_number < 5:
                yield self.retry_request(response.request)
            else:
                self.crawler.stats.inc_value('max_retries_reached')
            return
        if len(results) < self.max_urls:
            self.logger.warning(
                'Found fewer results (%s) on %s than max_urls=%s',
                len(results), response.url, self.max_urls
            )

        for index, result in enumerate(results):

            if index >= self.max_urls:
                break
            item = avc.items.GoogleNewsItem()
            date_raw = result.xpath(".//span[contains(text(),'ago')]/text()").get('')
            if date_raw:
                item['article_date'] = str(dateparser.parse(date_raw)).split('.')[0]
            
            item['first_paragraph'] = ''.join(result.xpath('.//*[@role="heading"]/parent::*/div[3]/div[1]//text()').getall()).strip().replace('\n','')

            item['headline'] = ''.join(result.css('[role="heading"]::text').getall()).replace('\n','')

            item['keywords'] = response.meta['keyword']

            item['news_url'] = result.css('a::attr(href)').extract_first()

            item['position'] = index + 1

            item['search_url'] = response.url
            if item['news_url']:
                parsed = urllib.parse.urlparse(item['news_url'])
                item['website'] = urllib.parse.urlunparse(parsed._replace(
                    path='/', params='', query='', fragment=''
                ))

            if self.excluded_domains:
                drop_item = False
                parsed = urllib.parse.urlparse(item['news_url'])
                for domain in self.excluded_domains:
                    if domain == parsed.netloc or parsed.netloc.endswith('.%s' % domain):
                        self.logger.debug(
                            'Dropping item due to excluded domain: %s',
                            item
                        )
                        self.crawler.stats.inc_value('items/dropped/domain')
                        drop_item = True
                        break
                if drop_item:
                    continue

            yield scrapy.Request(url=item['news_url'], callback=self.parse_item_status, meta={ 'item': item, 'keywords':item['keywords'] })

    def parse_item_status(self, response):

        item = response.meta['item']
        
        full_data = response.text
        full_data = full_data.lower()
        keywords = response.meta['keywords']
        key_list = keywords.split(',')
            
        item_status = []

        for key in key_list: 
            key = key.lower()
            key = key.replace('"', '') 
            item_exists = key in full_data
            item_status.append(item_exists)

        yield_status = all(item_status)

        if yield_status:
            yield item
                
    @staticmethod
    def retry_request(request):
        new_request = request.copy()
        new_request.meta['_retry_times'] = new_request.meta.get('_retry_times', 0) + 1
        new_request.dont_filter = True
        return new_request
