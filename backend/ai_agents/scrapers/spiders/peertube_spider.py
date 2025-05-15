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
    custom_settings = { # Spider-specific settings can override project settings
        'DOWNLOAD_DELAY': 1.5, # Slightly more polite for this specific spider
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    }

    def __init__(self, start_url=None, target_domain=None, search_query=None, max_items_to_scrape=10, *args, **kwargs):
        super(PeertubeSpider, self).__init__(*args, **kwargs)
        
        self.search_query = search_query
        self.max_items = int(max_items_to_scrape)
        self.item_count = 0

        if start_url:
            self.start_urls = [start_url]
            self.allowed_domains = [target_domain if target_domain else urlparse(start_url).netloc]
            self.logger.info(f"PeertubeSpider initialized for Start URL: {start_url}, Domain: {self.allowed_domains}, Max Items: {self.max_items}, Query: {self.search_query}")
        else:
            self.logger.error("PeertubeSpider: Critical - No start_url provided!")
            self.start_urls = [] # Prevent crawling if not properly initialized

    def parse(self, response):
        """
        Parses video listing pages (e.g., search results, /videos/local, etc.).
        """
        if not self.start_urls: # Spider wasn't initialized with a URL
            return

        self.logger.info(f"Parsing listing page: {response.url}. Items scraped so far: {self.item_count}/{self.max_items}")

        # === YOU MUST REPLACE THESE SELECTORS WITH ACTUAL ONES FOR YOUR TARGET PEERTUBE INSTANCE ===
        # Example: Common structure for video miniatures in PeerTube themes
        video_miniatures = response.css('div.video-miniature, div.video-tile, article.video-card, div.videos-grid-item') 

        if not video_miniatures:
            self.logger.warning(f"No video miniatures found on {response.url} with current selectors. Check selectors.")
            # Try a very generic link finder if specific ones fail (less reliable)
            # video_miniatures = response.css('a[href*="/w/"], a[href*="/videos/watch/"]')


        for miniature in video_miniatures:
            if self.item_count >= self.max_items:
                self.logger.info(f"Max items ({self.max_items}) reached. Stopping crawl of listing page.")
                return

            # Extract relative URL to the video page
            relative_video_url = miniature.css('a.video-link::attr(href), a.thumbnail::attr(href), a::attr(href)').get() # Try common patterns
            
            if relative_video_url:
                # Filter out non-video links if a generic selector was used
                if not ('/w/' in relative_video_url or '/videos/watch/' in relative_video_url or '/videos/embed/' in relative_video_url):
                    # self.logger.debug(f"Skipping non-video link: {relative_video_url}")
                    continue

                full_video_url = response.urljoin(relative_video_url)
                # Check if we already visited or scheduled this to avoid loops on same page links
                yield scrapy.Request(full_video_url, callback=self.parse_video_page)
            # else:
                # self.logger.debug(f"No video link found in a miniature block on {response.url}")

        # === PAGINATION LOGIC (EXAMPLE - HIGHLY SITE-SPECIFIC) ===
        # next_page_candidates = response.css('ul.pagination li.active + li a::attr(href), a.pagination-next::attr(href), a[rel="next"]::attr(href)')
        # next_page = next_page_candidates.get()
        # if next_page and self.item_count < self.max_items:
        #     self.logger.info(f"Following next page: {next_page}")
        #     yield response.follow(next_page, callback=self.parse)


    def parse_video_page(self, response):
        if self.item_count >= self.max_items:
            self.logger.info(f"Max items ({self.max_items}) reached before parsing video page. Skipping {response.url}")
            return

        self.logger.info(f"Parsing video page: {response.url}")
        loader = ItemLoader(item=PapriVideoItem(), response=response)

        loader.add_value('original_url', response.url)
        loader.add_value('platform_name', f'PeerTube_{self.allowed_domains[0]}') # Use the specific instance domain

        # Video ID extraction from URL
        url_path = urlparse(response.url).path
        video_id = None
        if '/w/' in url_path: video_id = url_path.split('/w/')[-1].split('?')[0].split('/')[0]
        elif '/videos/watch/' in url_path: video_id = url_path.split('/videos/watch/')[-1].split('?')[0].split('/')[0]
        elif '/videos/embed/' in url_path: video_id = url_path.split('/videos/embed/')[-1].split('?')[0].split('/')[0]
        
        if not video_id: # Attempt to get from meta tags if URL is unusual
            video_id = response.xpath('//meta[@property="og:url"]/@content').re_first(r'/w/([a-zA-Z0-9_-]+)|/videos/watch/([a-zA-Z0-9_-]+)|/videos/embed/([a-zA-Z0-9_-]+)')
            if isinstance(video_id, list): video_id = next(filter(None, video_id), None)

        if not video_id: self.logger.warning(f"Could not determine platform_video_id for {response.url}")
        loader.add_value('platform_video_id', video_id)
        
        # === YOU MUST REPLACE THESE SELECTORS WITH ACTUAL ONES ===
        loader.add_css('title', 'h1.video-title::text, meta[property="og:title"]::attr(content), title::text')
        loader.add_css('description', 'div.video-description .markdown p::text, div.video-description::text, meta[property="og:description"]::attr(content)')
        loader.add_xpath('thumbnail_url', '//meta[@property="og:image"]/@content')
        
        loader.add_xpath('publication_date_str', '//meta[@itemprop="uploadDate"]/@content, //meta[@property="video:release_date"]/@content')
        if not loader.get_collected_values('publication_date_str'): # Alternate common way
            loader.add_css('publication_date_str', 'span.date-label time::attr(datetime), p. वीडियो-publication-date::text')

        loader.add_xpath('duration_str', '//meta[@itemprop="duration"]/@content') # e.g., PT10M3S
        
        loader.add_css('uploader_name', 'a.video-channel-name .instance-actor-name::text, a.video-channel-info .display-name::text, .channel-name a::text')
        loader.add_css('uploader_url', 'a.video-channel-name::attr(href), a.video-channel-info .display-name::attr(href)')
        
        loader.add_css('tags', 'div.video-tags a.tag::text, .tags a::text') # Common tag structures

        # VTT URL (crucial)
        # Try to find English first, then any other caption track
        vtt_en_url = response.xpath('//video//track[@kind="captions" and (@srclang="en" or starts-with(@srclang, "en-"))][1]/@src').get()
        if vtt_en_url:
            loader.add_value('transcript_vtt_url', response.urljoin(vtt_en_url))
            loader.add_value('language_code', 'en') # Assume English
        else:
            any_vtt_url = response.xpath('//video//track[@kind="captions"][1]/@src').get()
            if any_vtt_url:
                loader.add_value('transcript_vtt_url', response.urljoin(any_vtt_url))
                # Try to get language code from srclang attribute
                lang = response.xpath('//video//track[@kind="captions"][1]/@srclang').get()
                loader.add_value('language_code', lang if lang else 'und') # 'und' for undetermined

        # Embed URL / Direct Video URLs
        loader.add_xpath('embed_url', '//meta[@itemprop="embedURL"]/@content, //link[@itemprop="embedUrl"]/@href')
        loader.add_xpath('direct_video_url', '//video/source[@type="video/mp4"][1]/@src, //video/source[1]/@src') # Prioritize MP4

        item = loader.load_item()
        
        # Basic check if essential data was scraped
        if item.get('title') and item.get('original_url'):
            self.item_count += 1
            yield item
        else:
            self.logger.warning(f"Essential data (title/url) missing for {response.url}. Item not yielded.")
