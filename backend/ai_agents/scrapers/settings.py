# backend/ai_agents/scrapers/settings.py
BOT_NAME = 'papri_search_agent_scraper'
SPIDER_MODULES = ['spiders']
NEWSPIDER_MODULE = 'spiders'
ROBOTSTXT_OBEY = False # SET TO TRUE AND VERIFY IN PRODUCTION! 
USER_AGENT = 'PapriSearchBot/1.0 (+https://www.your-papri-domain.com/botinfo.html)' # CHANGE THIS 

# Configure item pipelines if you add any (e.g., for data cleaning, validation)
ITEM_PIPELINES = {
   'scrapers.pipelines.YourPipeline': 300,
}
USER_AGENT = 'PapriSearchBot/1.0 (+https://www.your-papri-domain.com/botinfo.html)' # CHANGE THIS 
DOWNLOAD_DELAY = 1.5
CONCURRENT_REQUESTS_PER_DOMAIN = 2 # Further reduced for politeness
AUTOTHROTTLE_ENABLED = True # 
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60 # Increased max delay
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0 # More conservative
LOG_LEVEL = 'INFO'
LOG_FILE = 'scrapy_log.txt' # To output Scrapy logs to a file

PCACHE_EXPIRATION_SECS = 0 # Infinite cache until manually cleared (not for dynamic sites)
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

