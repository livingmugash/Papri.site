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
    custom_settings = {
        'DOWNLOAD_DELAY': 2, # Increased default delay
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 30,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'USER_AGENT': 'PapriSearchBot/1.0 (+https://www.yourpaprisite.com/botinfo.html)' # CHANGE THIS URL
    }

    def __init__(self, start_url=None, target_domain=None, search_query=None, max_items_to_scrape=10, *args, **kwargs):
        super(PeertubeSpider, self).__init__(*args, **kwargs)
        
        self.search_query = search_query
        self.max_items = int(max_items_to_scrape)
        self.scraped_item_count = 0 # Renamed for clarity

        if start_url:
            self.start_urls = [start_url]
            # Ensure allowed_domains is a list of strings
            self.allowed_domains = [target_domain if target_domain else urlparse(start_url).netloc]
            logger.info(f"PeertubeSpider initialized. Start URL: {start_url}, Domain: {self.allowed_domains}, Max Items: {self.max_items}, Query: '{self.search_query}'")
        else:
            logger.error("PeertubeSpider: Critical - No start_url provided!")
            self.start_urls = []

    def parse_ld_json_data(self, response):
        """Helper to extract data from ld+json scripts."""
        ld_json_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        video_data = {}
        for script_content in ld_json_scripts:
            try:
                data = json.loads(script_content)
                # Look for VideoObject, typically it's a list or a single object
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']:
                            video_data = item; break
                elif isinstance(data, dict) and data.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']:
                    video_data = data
                
                if video_data: # Found a VideoObject
                    logger.debug(f"Found LD+JSON VideoObject on {response.url}")
                    return video_data
            except json.JSONDecodeError:
                logger.warning(f"Could not parse LD+JSON on {response.url}: {script_content[:100]}...")
            except Exception as e:
                logger.error(f"Unexpected error parsing LD+JSON on {response.url}: {e}")
        return None # Return None if no suitable VideoObject found

    def parse(self, response):
        if not self.start_urls: return
        logger.info(f"Parsing listing page: {response.url}. Items scraped: {self.scraped_item_count}/{self.max_items}")

        # === COMMON PEERTUBE SELECTORS FOR VIDEO LINKS ON LISTING PAGES ===
        # These are examples. Inspect your target instance.
        # Look for containers holding video miniatures/tiles/cards.
        # Common classes: 'video-miniature-container', 'video-miniature', 'video-tile', 'card', 'videos-grid-item'
        # Common link classes within them: 'video-link', 'thumbnail', or just the first `a` tag.
        
        # Try a few common patterns for video miniature containers/links:
        video_links_candidates = [
            'div.videos-list-results-videos div.video-miniature a.video-link::attr(href)', # Common in search/list views
            'div.video-miniature-container a.video-link::attr(href)',
            'figure.video-miniature a.video-link-miniature::attr(href)',
            'div.video-block a::attr(href)', # More generic
            'article.video-card a.card-link::attr(href)', # Another theme pattern
        ]
        
        video_hrefs = []
        for selector in video_links_candidates:
            video_hrefs = response.css(selector).getall()
            if video_hrefs:
                logger.debug(f"Found {len(video_hrefs)} links with selector: {selector}")
                break # Found links with this selector

        if not video_hrefs:
             logger.warning(f"No video links found on listing page {response.url} with current selectors. Please check/update spider selectors.")


        for href in video_hrefs:
            if self.scraped_item_count >= self.max_items:
                logger.info(f"Max items ({self.max_items}) reached from listing page. Stopping.")
                return

            full_video_url = response.urljoin(href)
            # Basic check to ensure it looks like a video page URL for PeerTube
            if '/w/' in full_video_url or '/videos/watch/' in full_video_url or '/videos/embed/' in full_video_url:
                yield scrapy.Request(full_video_url, callback=self.parse_video_page)
            # else:
                # logger.debug(f"Skipping non-standard video link from listing: {full_video_url}")

        # === PAGINATION (HIGHLY SITE-SPECIFIC) ===
        # Example selectors for "next page" links.
        # next_page_sel = 'ul.pagination li.active + li:not(.disabled) a::attr(href), a.pagination-next::attr(href), a[rel="next"]::attr(href)'
        # next_page = response.css(next_page_sel).get()
        # if next_page and self.scraped_item_count < self.max_items:
        #     logger.info(f"Following next page: {next_page}")
        #     yield response.follow(next_page, callback=self.parse)


    def parse_video_page(self, response):
        if self.scraped_item_count >= self.max_items:
            logger.info(f"Max items ({self.max_items}) reached. Skipping video page: {response.url}")
            return

        logger.info(f"Parsing video page: {response.url}")
        
        # Try to get data from LD+JSON first, as it's often more structured
        ld_data = self.parse_ld_json_data(response)
        if ld_data: logger.info(f"Extracted LD+JSON data for {response.url}")
        else: ld_data = {} # Ensure ld_data is a dict even if None

        loader = ItemLoader(item=PapriVideoItem(), response=response)
        loader.add_value('original_url', response.url)
        loader.add_value('instance_url', f"{response.urlparts.scheme}://{response.urlparts.netloc}")
        loader.add_value('platform_name', f'PeerTube_{response.urlparts.netloc}')

        # Video ID (Robust extraction)
        url_path = response.urlparts.path
        video_id = None
        # Common PeerTube URL patterns: /w/shortId, /videos/watch/UUID, /videos/embed/UUID
        # The shortId can be alphanumeric, UUID is hex with hyphens.
        match_uuid = re.search(r'/(?:videos/watch/|videos/embed/|w/)(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', url_path)
        if match_uuid: video_id = match_uuid.group('id')
        else:
            match_short_id = re.search(r'/w/(?P<id>[a-zA-Z0-9_-]+)', url_path) # Alphanumeric, underscore, hyphen
            if match_short_id: video_id = match_short_id.group('id')
        
        if not video_id: video_id = ld_data.get('identifier') # From LD+JSON
        if not video_id: video_id = response.xpath('//meta[@itemprop="identifier"]/@content').get() # From meta
        if not video_id: logger.warning(f"Could not reliably determine platform_video_id for {response.url}")
        loader.add_value('platform_video_id', video_id)

        # --- METADATA EXTRACTION (Prioritize LD+JSON, then meta tags, then CSS/XPath) ---
        loader.add_value('title', ld_data.get('name') or response.xpath('//meta[@property="og:title"]/@content').get() or response.css('h1.video-title::text, h1.title::text, .video-title h1::text').get())
        loader.add_value('description', ld_data.get('description') or response.xpath('//meta[@property="og:description"]/@content').get() or response.css('div.video-description .markdown ::text, div.description ::text').getall()) # getall for multi-p
        loader.add_value('thumbnail_url', ld_data.get('thumbnailUrl') or response.xpath('//meta[@property="og:image"]/@content').get())
        
        loader.add_value('publication_date_str', ld_data.get('uploadDate') or ld_data.get('datePublished') or response.xpath('//meta[@itemprop="uploadDate"]/@content').get() or response.css('span.date-label time::attr(datetime), .upload-date::text').get())
        loader.add_value('duration_str', ld_data.get('duration') or response.xpath('//meta[@itemprop="duration"]/@content').get()) # ISO 8601 format like PT10M3S

        # Uploader/Channel Info (Can be complex)
        uploader_info = ld_data.get('author') or ld_data.get('channel') # LD+JSON often has author/channel as an object
        if isinstance(uploader_info, dict):
            loader.add_value('uploader_name', uploader_info.get('name'))
            loader.add_value('uploader_url', uploader_info.get('url') or uploader_info.get('@id'))
        else:
            loader.add_css('uploader_name', 'a.video-channel-name .instance-actor-name::text, a.video-channel-name .user-name::text, .video-channel .channel-name a::text')
            loader.add_css('uploader_url', 'a.video-channel-name::attr(href), .video-channel .channel-name a::attr(href)')

        loader.add_value('tags', ld_data.get('keywords') or response.css('div.video-tags a.tag::text, .tags a::text').getall()) # Often a comma-separated string or list in LD+JSON
        
        loader.add_value('view_count_str', ld_data.get('interactionStatistic', {}).get('userInteractionCount') or response.xpath('//meta[@itemprop="interactionCount"]/@content').get() or response.css('.views-count::text, .view-count::text').re_first(r'(\d[\d,\.]*)'))
        loader.add_value('like_count_str', response.css('.likes-count::text, .like-count::text').re_first(r'(\d[\d,\.]*)')) # Often dynamic

        # Extract from PeerTube specific attributes in your PDF if selectors are known
        # loader.add_value('language_code_video', response.xpath('//meta[@itemprop="inLanguage"]/@content').get() or ld_data.get('inLanguage'))
        # loader.add_value('licence_str', ld_data.get('license') or response.xpath('//a[contains(@href, "/videos/licences/")]/text()').get())
        # loader.add_value('category_str', ld_data.get('genre') or response.xpath('//div[contains(@class, "video-category")]/a/text()').get())
        # loader.add_value('privacy_str', response.xpath('//meta[@itemprop="is семейный"]/@content').get()) # Example, needs actual field for privacy

        # Transcript/Caption VTT URL
        # Try English, then any. Ensure full URL.
        vtt_path_en = response.xpath('//video//track[@kind="captions" and (@srclang="en" or starts-with(@srclang, "en-"))][1]/@src').get()
        lang_code_cap = "en" if vtt_path_en else None
        vtt_path_any = response.xpath('//video//track[@kind="captions"][1]/@src').get()
        if not lang_code_cap and vtt_path_any:
            lang_code_cap = response.xpath('//video//track[@kind="captions"][1]/@srclang').get() or 'und'

        final_vtt_path = vtt_path_en or vtt_path_any
        if final_vtt_path:
            loader.add_value('transcript_vtt_url', response.urljoin(final_vtt_path))
            loader.add_value('language_code_caption', lang_code_cap)
        
        loader.add_value('embed_url', ld_data.get('embedUrl') or response.xpath('//meta[@itemprop="embedURL"]/@content').get())
        loader.add_value('direct_video_url', response.xpath('//video/source[@type="video/mp4"][1]/@src').get() or response.xpath('//video/source[1]/@src').get()) # Prioritize MP4

        loader.add_value('ld_json_data', ld_json_scripts[0] if 'ld_json_scripts' in locals() and ld_json_scripts else None) # Store the first full LD+JSON script

        item = loader.load_item()
        if item.get('title') and item.get('original_url') and item.get('platform_video_id'):
            self.scraped_item_count += 1
            yield item
        else:
            logger.warning(f"Essential data (title/url/platform_id) missing for {response.url}. Item not yielded. Title: {item.get('title')}, PlatformID: {item.get('platform_video_id')}")
