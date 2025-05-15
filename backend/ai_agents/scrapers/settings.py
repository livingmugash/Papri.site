# backend/ai_agents/scrapers/settings.py
# For Scrapy to find items.py correctly when run via subprocess from SOIAgent
# This assumes items.py is in the same directory as this settings.py or one level up.
# If items.py is in 'scrapers/' directory:
# ITEM_PIPELINES = {} # Define if you have pipelines
# SPIDER_MODULES = ['scrapers.spiders']
# NEWSPIDER_MODULE = 'scrapers.spiders'

# A simpler way if items.py is directly accessible via PYTHONPATH set by Django
# is sometimes enough, or ensure the CWD for subprocess is correct.
# If running 'scrapy crawl' from self.scrapers_base_dir and items.py is in scrapers/items.py,
# then an import like `from ..items import PapriVideoItem` in the spider should work
# if scrapers_base_dir is added to sys.path or if scrapers is a package.

# For standalone spiders, we often don't need a full settings.py if items are imported relatively.
# The main thing is that the `scrapy crawl` command can find the spider and its item definition.
# If you use `PYTHONPATH=. scrapy crawl ...` from the `backend` dir, then `from ai_agents.scrapers.items import PapriVideoItem` might work.
# For the current subprocess call from SOIAgent (cwd=self.scrapers_base_dir),
# the spider `from ..items import PapriVideoItem` implies items.py is in `ai_agents/scrapers/`
# Let's ensure that.

# Minimal settings if needed:
BOT_NAME = 'papri_scraper'
SPIDER_MODULES = ['spiders'] # Assumes spiders are in a 'spiders' subdirectory of where scrapy is run
NEWSPIDER_MODULE = 'spiders'
ROBOTSTXT_OBEY = False # Set to True to obey robots.txt (recommended for general scraping)
                      # For specific targets, you might override this in spider or command.
USER_AGENT = 'PapriSearchBot/1.0 (+http://www.yourpaprisite.com/bot.html)' # Be a good bot
DOWNLOAD_DELAY = 0.5 # Basic courtesy delay
# CONCURRENT_REQUESTS_PER_DOMAIN = 8
