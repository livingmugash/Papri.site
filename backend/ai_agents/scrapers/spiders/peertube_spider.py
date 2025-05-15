# backend/ai_agents/scrapers/spiders/peertube_spider.py
import scrapy
from scrapy.loader import ItemLoader
# Define an Item for scraped data (can be in a separate items.py)

class PapriVideoItem(scrapy.Item):
    original_url = scrapy.Field()
    platform_name = scrapy.Field()
    platform_video_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    thumbnail_url = scrapy.Field()
    publication_date_str = scrapy.Field() # String format from site
    duration_str = scrapy.Field() # String format from site (e.g., "10:35")
    uploader_name = scrapy.Field()
    uploader_url = scrapy.Field()
    tags = scrapy.Field() # list of strings
    view_count_str = scrapy.Field()
    like_count_str = scrapy.Field()
    # For transcripts/captions
    transcript_text = scrapy.Field()
    transcript_vtt_url = scrapy.Field()
    # Embed URL or direct video file URL
    embed_url = scrapy.Field()
    direct_video_url = scrapy.Field()


Okay, "let's proceed"!

We've just outlined the initial steps for incorporating web scraping into the SourceOrchestrationAgent (SOIAgent), including a conceptual Scrapy spider for PeerTube and how the SOIAgent might run it. This is a significant move towards Papri's goal of comprehensive source coverage.

The immediate "next" after setting up the framework for scraping is to:

Make a specific Scrapy spider functional for one chosen platform. This means selecting a real, public PeerTube instance (or another suitable "alternative" platform that typically requires scraping), thoroughly inspecting its HTML structure, and writing the correct CSS/XPath selectors in our PeertubeSpider (or a new, similarly structured spider).
Test this specific spider standalone to ensure it correctly extracts the PapriVideoItem data.
Integrate and test the execution of this functional spider via SOIAgent to see if its results are correctly processed and make their way into the Papri database and search results.
This is a very practical, hands-on step.

Let's assume for this step you've chosen a specific PeerTube instance to target for our first scraper. For example, let's say we're targeting https://tilvids.com (a PeerTube instance focused on educational content - always remember to check robots.txt and terms of service before scraping any site).

Step 33: Develop and Test a Functional Scrapy Spider for a Chosen Platform (e.g., Tilvids.com)

1. Analyze Target Site Structure (e.g., Tilvids.com)

Video Listing Page: Go to a page like https://tilvids.com/videos/local or https://tilvids.com/videos/trending. Use your browser's developer tools to "Inspect" the elements.
Find the common container for each video preview.
Within that container, find the <a> tag whose href attribute leads to the individual video page.
Individual Video Page: Navigate to a specific video (e.g., from the link you found).
Title: Usually in an <h1> or <h2> tag with a specific class.
Description: Often in a <div> with a class like video-description or markdown.
Uploader/Channel: Look for links to the channel/uploader page and their name.
Publication Date: Often in a <time> tag with a datetime attribute, or a <span> with a specific class.
Duration: Might be in a <meta itemprop="duration" content="PTxMxS"> tag, or displayed visually.
Thumbnail: Often in <meta property="og:image" content="..."> or a main <img> tag for the video.
Tags: Usually a list of <a> tags with a class like tag.
View Count/Likes: These can be tricky as they might be loaded dynamically by JavaScript after the initial HTML. You might need to look at network requests or JavaScript variables if not directly in the static HTML. Scrapy might not get these easily without Splash/Selenium if they are JS-rendered.
Captions/Transcripts (VTT files): This is crucial. Look in the HTML for <track kind="captions" src="..."> elements within a <video> tag. Or, inspect network requests when the video plays to see if .vtt files are loaded. The URL in src is what you need.
Embed URL/Direct Video File: <meta itemprop="embedUrl" ...> or <video><source src="..."></video>.
2. Update the Scrapy Spider (backend/ai_agents/scrapers/spiders/peertube_spider.py) with Real Selectors

Let's assume we are targeting tilvids.com and have found some (example) selectors. You will need to replace these with the actual selectors you find.

Python

# backend/ai_agents/scrapers/spiders/peertube_spider.py
import scrapy
from scrapy.loader import ItemLoader
from urllib.parse import urlparse # For allowed_domains
from ..items import PapriVideoItem # Assuming items.py is in .. (one level up)

# Create backend/ai_agents/scrapers/items.py:
# import scrapy
# class PapriVideoItem(scrapy.Item):
#     original_url = scrapy.Field(); platform_name = scrapy.Field(); platform_video_id = scrapy.Field()
#     title = scrapy.Field(); description = scrapy.Field(); thumbnail_url = scrapy.Field()
#     publication_date_str = scrapy.Field(); duration_str = scrapy.Field()
#     uploader_name = scrapy.Field(); uploader_url = scrapy.Field(); tags = scrapy.Field()
#     view_count_str = scrapy.Field(); like_count_str = scrapy.Field()
#     transcript_text = scrapy.Field(); transcript_vtt_url = scrapy.Field()
#     embed_url = scrapy.Field(); direct_video_url = scrapy.Field()


class PeertubeSpider(scrapy.Spider):
    name = "peertube"
    # This spider is now more tailored. It might not need 'query_text' directly
    # if it's just Browse, or it could construct a search URL.

    def __init__(self, start_url=None, target_domain=None, search_query=None, *args, **kwargs):
        super(PeertubeSpider, self).__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]
            self.allowed_domains = [target_domain if target_domain else urlparse(start_url).netloc]
        else:
            # Default for testing specific instance if not provided by agent
            # self.start_urls = ['https://tilvids.com/videos/recently-added'] # Example for Tilvids
            # self.allowed_domains = ['tilvids.com']
            self.logger.warning("PeertubeSpider: No start_url provided during initialization!")
            self.start_urls = []
        
        self.search_query = search_query # Store query if spider logic uses it (e.g. for constructing search URLs)
        self.item_count = 0
        self.max_items = kwargs.get('max_items_to_scrape', 20) # Max items to scrape per run

    def parse(self, response):
        """
        Parses video listing pages (e.g., /videos/local, /videos/trending, or search results page).
        Extracts links to individual video pages.
        """
        self.logger.info(f"Parsing listing page: {response.url}")

        # --- SELECTORS FOR TILVIDS.COM (EXAMPLE - VERIFY AND ADJUST) ---
        # Video items often in a list or grid
        # For tilvids.com, a common structure might be <div class="videos-grid"> ... <div class="video-block">
        video_blocks = response.css('div.video-miniature-container') # More generic PeerTube selector
        if not video_blocks:
            video_blocks = response.css('div.video-block') # Another common one
            if not video_blocks:
                 self.logger.warning(f"No video blocks found on {response.url} with common selectors.")

        for video_block in video_blocks:
            if self.item_count >= self.max_items:
                self.logger.info(f"Reached max items to scrape ({self.max_items}). Stopping.")
                return # Stop crawling this page further

            # Get the link to the individual video page
            relative_video_url = video_block.css('a.video-link::attr(href)').get() # Common class
            if not relative_video_url:
                 relative_video_url = video_block.css('a::attr(href)').get() # More generic link if above fails

            if relative_video_url:
                full_video_url = response.urljoin(relative_video_url)
                yield scrapy.Request(full_video_url, callback=self.parse_video_page)
            else:
                self.logger.warning(f"Could not find video link in block on {response.url}")
        
        # --- PAGINATION (EXAMPLE - VERIFY AND ADJUST) ---
        # next_page_link = response.css('ul.pagination li.pagination-next a::attr(href)').get()
        # if next_page_link and self.item_count < self.max_items:
        #     self.logger.info(f"Following next page: {next_page_link}")
        #     yield response.follow(next_page_link, callback=self.parse)


    def parse_video_page(self, response):
        """
        Parses an individual video page to extract metadata.
        """
        if self.item_count >= self.max_items:
            self.logger.info(f"Reached max items ({self.max_items}) before parsing video page. Skipping {response.url}")
            return

        self.logger.info(f"Parsing video page: {response.url}")
        loader = ItemLoader(item=PapriVideoItem(), response=response)

        loader.add_value('original_url', response.url)
        loader.add_value('platform_name', 'PeerTube_' + self.allowed_domains[0]) # e.g., PeerTube_tilvids.com

        # Extract video ID from URL (e.g., /w/shortVideoId or /videos/watch/uuid-video-id)
        url_path = urlparse(response.url).path
        if '/w/' in url_path:
            video_id = url_path.split('/w/')[-1].split('?')[0]
        elif '/videos/watch/' in url_path:
            video_id = url_path.split('/videos/watch/')[-1].split('?')[0]
        else:
            video_id = None # Fallback needed
            self.logger.warning(f"Could not determine platform_video_id from URL: {response.url}")
        loader.add_value('platform_video_id', video_id)
        
        # --- SELECTORS FOR TILVIDS.COM (EXAMPLE - VERIFY AND ADJUST) ---
        loader.add_css('title', 'h1.video-title::text, meta[property="og:title"]::attr(content)')
        loader.add_css('description', 'div.video-description div.markdown p::text, meta[property="og:description"]::attr(content)')
        loader.add_xpath('thumbnail_url', '//meta[@property="og:image"]/@content')
        
        # Publication date often in a <meta> or <time> tag, or sometimes in ld+json script
        loader.add_xpath('publication_date_str', '//meta[@itemprop="uploadDate"]/@content')
        # if not loader.get_output_value('publication_date_str'):
        #     loader.add_css('publication_date_str', 'span.date-label time::attr(datetime)') # Another common pattern

        # Duration often in <meta itemprop="duration">
        loader.add_xpath('duration_str', '//meta[@itemprop="duration"]/@content') # e.g., PT10M3S
        
        loader.add_css('uploader_name', 'a.video-channel-name span.username::text, div.video-account span.actor-name span::text')
        loader.add_css('uploader_url', 'a.video-channel-name::attr(href), div.video-account a.display-name::attr(href)')
        
        loader.add_css('tags', 'div.video-tags a.tag-饅頭::text') # Check for tag specific classes

        # View count can be tricky, often JS rendered. Look for static counts if available.
        # loader.add_css('view_count_str', '.views-count::text, .view-count::text') 
        
        # Transcripts/Captions (VTT files)
        # Look for <track kind="captions" src="URL_TO_VTT_FILE.vtt" srclang="en">
        # Or in <script type="application/ld+json"> for videoObject.transcript
        # This selector gets the src from the first English caption track
        loader.add_xpath('transcript_vtt_url', '//video//track[@kind="captions" and (@srclang="en" or @srclang="en-US")][1]/@src')
        # Fallback if no English:
        if not loader.get_output_value('transcript_vtt_url'):
             loader.add_xpath('transcript_vtt_url', '//video//track[@kind="captions"][1]/@src')


        # Embed URL or direct video file
        loader.add_xpath('embed_url', '//meta[@itemprop="embedURL"]/@content')
        if not loader.get_output_value('embed_url'):
             loader.add_css('embed_url', 'link[itemprop="embedUrl"]::attr(href)')
        
        # Try to get a direct MP4 link if possible from <video> <source>
        loader.add_xpath('direct_video_url', '//video/source[@type="video/mp4"][1]/@src')


        self.item_count += 1
        yield loader.load_item()

# To run from command line for testing this spider:
# Assuming this file is in backend/ai_agents/scrapers/spiders/peertube_spider.py
# And items.py is in backend/ai_agents/scrapers/items.py
# And you are in the 'backend' directory:
# PYTHONPATH=. scrapy crawl peertube -a start_url="https://tilvids.com/videos/recently-
