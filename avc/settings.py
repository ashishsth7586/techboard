# -*- coding: utf-8 -*-

# Scrapy settings for avc project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

import requests
from datetime import datetime

BOT_NAME = 'avc'

SPIDER_MODULES = ['avc.spiders']
NEWSPIDER_MODULE = 'avc.spiders'

ITEM_PIPELINES = {
   'avc.pipelines.SetCrawlTimePipeline': 300,
   'avc.pipelines.S3Pipeline': 1
}

HS_AUTH = '11da154e98d349979032b1fc46506293'
HS_PROJECTID = '88980'

FACEBOOK_APP_ID = '716022795220055'
FACEBOOK_APP_SECRET = 'e2287eb12a43bad38428426325781f72'
FACEBOOK_USER_TOKEN = ''
TWITTER_CONSUMER_KEY = 'PtfU3iET4t2MQnz7QHk4Rx0W8'
TWITTER_CONSUMER_SECRET = 'jPhyyLD0vSm7uDTuMNixYJwjgVQVLES2sdnHAOKS5e9kkh2KIq'
TWITTER_ACCESS_TOKEN = '21738476-wHrwSanbw0sAYmr5IiG5jrusZE7LMiywfUsESOqWQ'
TWITTER_ACCESS_SECRET = 'Qzon1GxNkfROpPuFV6lGtSGLsybRTcQ7S7w7Tmo3Ubkm3'

AVC_MIN_POST_DATE = '2016-01-01'
AVC_DATE_FORMAT = '%Y-%m-%d'
AVC_DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

# ROTATING_PROXY_LIST = [
#     '204.15.243.233:35899',
#     # ...
# ]

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'avc (+http://www.yourdomain.com)'

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'avc.middlewares.MyCustomSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
#     'rotating_proxies.middlewares.BanDetectionMiddleware': 620,
#    #'avc.middlewares.MyCustomDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
HTTPCACHE_ENABLED = False
#REDIRECT_ENABLED = False
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
CRAWLERA_ENABLED = True
CRAWLERA_APIKEY = 'c20577a553094e76b4cd6aaa59236d36'

AWS_ACCESS_KEY_ID = 'AKIAYJUCMZICI27RGFUO'
AWS_SECRET_ACCESS_KEY = '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'
AWS_REGION_NAME = 'ap-southeast-2' 
#r = requests.get('http://13.55.163.121:6800/listjobs.json?project=avc')
#print('getting job id to paste in ')
#print(r.json()['running'])
JOB_TIMESTAMP = datetime.today().strftime('%Y-%m-%d_%H:%M')
FEED_URI = 's3://scrapy-admin/results/'+JOB_TIMESTAMP+'.csv'
S3PIPELINE_URL = FEED_URI
FEED_FORMAT = 'csv'
FEED_EXPORT_FIELDS = None
FEED_STORE_EMPTY = False
FEED_STORAGES = {}
FEED_STORAGES_BASE = { 
'': None,
'file': None,
'stdout': None,
's3': 'scrapy.extensions.feedexport.S3FeedStorage',
'ftp': None,
}
FEED_EXPORTERS = {
   'csv': 'scrapy.exporters.CsvItemExporter'
}
FEED_EXPORTERS_BASE = {
    'json': None,
    'jsonlines': None,
    'jl': None,
    'csv': None,
    'xml': None,
    'marshal': None,
    'pickle': None,
}
#DUPEFILTER_CLASS = 'scrapy.dupefilter.RFPDupeFilter'
#DUPEFILTER_DEBUG = True
