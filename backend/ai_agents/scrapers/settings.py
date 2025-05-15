BOT_NAME = 'papri_search_agent_scraper'

SPIDER_MODULES = ['spiders'] # Tells Scrapy to look in a 'spiders' subdirectory
NEWSPIDER_MODULE = 'spiders'

# Obey robots.txt rules - SET TO TRUE FOR ETHICAL SCRAPING IN PRODUCTION
# For development and specific targets where you've checked, you might set to False.
ROBOTSTXT_OBEY = False # BE MINDFUL OF THE TARGET SITE'S POLICY!

# Configure item pipelines if you add any (e.g., for data cleaning, validation)
ITEM_PIPELINES = {
   'scrapers.pipelines.YourPipeline': 300,
}

# Set a default user agent. It's good practice to identify your bot.
USER_AGENT = 'PapriSearchBot/1.0 (+http://www.yourpaprisite.com/botinfo.html)' # Replace with your actual info URL

# Configure a delay for requests for the same website (seconds)
DOWNLOAD_DELAY = 1 # Start with 1 second, adjust based on target site's tolerance
CONCURRENT_REQUESTS_PER_DOMAIN = 4 # Limit concurrent requests to any single domain

# Enable and configure HTTP caching (disabled by default)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0 # Infinite cache until manually cleared (not for dynamic sites)
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'

# Optional: Configure logging for Scrapy
LOG_LEVEL = 'INFO' # Or 'DEBUG' for more verbosity during development
LOG_FILE = 'scrapy_log.txt' # To output Scrapy logs to a file
