# backend/ai_agents/scrapers/spiders/peertube_spider.py
import scrapy
from scrapy.loader import ItemLoader
from urllib.parse import urlparse, urljoin
import json
import re
import logging
from ..items import PapriVideoItem

logger = logging.getLogger(__name__)

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
        self.scraped_item_count = 0

        if start_url:
            self.start_urls = [start_url]
            self.allowed_domains = [target_domain if target_domain else urlparse(start_url).netloc]
            logger.info(f"PeertubeSpider: Init. Start URL: {start_url}, Domain: {self.allowed_domains}, Max: {self.max_items}, Query: '{self.search_query}'")
        else:
            logger.error("PeertubeSpider: Critical - No start_url provided!")
            self.start_urls = []

    def parse_ld_json_data(self, response):
        # ... (Implementation from Step 36 - unchanged) ...
        ld_json_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for script_content in ld_json_scripts:
            try:
                data = json.loads(script_content)
                if isinstance(data, list): data = next((item for item in data if isinstance(item, dict) and item.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']), None)
                if isinstance(data, dict) and data.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']: return data
            except: pass
        return None

    def parse(self, response):
        if not self.start_urls: return
        logger.info(f"PeertubeSpider: Parsing listing: {response.url}. Scraped: {self.scraped_item_count}/{self.max_items}")

        # === YOU MUST REPLACE THESE SELECTORS WITH ACTUAL ONES FOR YOUR TARGET PEERTUBE INSTANCE ===
        # Example (these are common but WILL vary by theme):
        video_miniature_selectors = [
            'div.videos-list-results-videos div.video-miniature', 
            'div.video-miniature-container',
            'figure.video-miniature',
            'div.video-block', 
            'article.video-card',
            'div.videos-grid-item'
        ]
        miniatures = []
        for sel in video_miniature_selectors:
            miniatures = response.css(sel)
            if miniatures: break
        
        if not miniatures: logger.warning(f"No video miniatures found on {response.url} with current selectors.")

        for miniature in miniatures:
            if self.scraped_item_count >= self.max_items:
                logger.info(f"Max items ({self.max_items}) reached from listing. Stopping."); return

            # Example: get link from first `a` tag with an href within the miniature
            relative_video_url = miniature.css('a[href]::attr(href)').get()
            
            if relative_video_url:
                full_video_url = response.urljoin(relative_video_url)
                if '/w/' in full_video_url or '/videos/watch/' in full_video_url or '/videos/embed/' in full_video_url: # Basic sanity check
                    yield scrapy.Request(full_video_url, callback=self.parse_video_page, meta={'dont_redirect': True, 'handle_httpstatus_list': [301, 302, 307, 308]})

        # === PAGINATION (HIGHLY SITE-SPECIFIC - EXAMPLE) ===
        next_page = response.css('YOUR_SELECTOR_FOR_NEXT_PAGE_LINK::attr(href)').get()
         if next_page and self.scraped_item_count < self.max_items:
            yield response.follow(next_page, callback=self.parse)

    def parse_video_page(self, response):
        if self.scraped_item_count >= self.max_items:
            logger.info(f"Max items reached. Skipping video page: {response.url}"); return

        logger.info(f"PeertubeSpider: Parsing video page: {response.url}")
        ld_data = self.parse_ld_json_data(response) or {} # Ensure ld_data is a dict

        loader = ItemLoader(item=PapriVideoItem(), response=response)
        loader.add_value('original_url', response.url)
        loader.add_value('instance_url', f"{response.urlparts.scheme}://{response.urlparts.netloc}")
        loader.add_value('platform_name', f'PeerTube_{response.urlparts.netloc}')

        # Video ID (Robust extraction) - from Step 36
        # ... (video_id extraction logic using re.search on response.urlparts.path or ld_data) ...
        url_path = response.urlparts.path; video_id = None
        match_uuid = re.search(r'/(?:videos/watch/|videos/embed/|w/)(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', url_path)
        if match_uuid: video_id = match_uuid.group('id')
        else:
            match_short_id = re.search(r'/w/(?P<id>[a-zA-Z0-9_-]+)', url_path)
            if match_short_id: video_id = match_short_id.group('id')
        if not video_id: video_id = ld_data.get('identifier') or response.xpath('//meta[@itemprop="identifier"]/@content').get()
        loader.add_value('platform_video_id', video_id)
        
        # --- REPLACE WITH YOUR ACTUAL SELECTORS based on your PDF and site inspection ---
        loader.add_value('title', ld_data.get('name') or response.xpath('YOUR_SELECTOR_FOR_OG_TITLE/@content').get() or response.css('YOUR_SELECTOR_FOR_H1_TITLE::text').get())
        loader.add_value('description', ld_data.get('description') or response.xpath('YOUR_SELECTOR_FOR_OG_DESCRIPTION/@content').get() or response.css('YOUR_SELECTOR_FOR_DESCRIPTION ::text').getall())
        loader.add_value('thumbnail_url', ld_data.get('thumbnailUrl') or response.xpath('YOUR_SELECTOR_FOR_OG_IMAGE/@content').get())
        
        pub_date = ld_data.get('uploadDate') or ld_data.get('datePublished') or response.xpath('YOUR_SELECTOR_FOR_UPLOAD_DATE_META/@content').get() or response.css('YOUR_SELECTOR_FOR_DATE_DISPLAY::attr(datetime)').get() or response.css('YOUR_SELECTOR_FOR_DATE_DISPLAY::text').get()
        loader.add_value('publication_date_str', pub_date)
        
        duration = ld_data.get('duration') or response.xpath('YOUR_SELECTOR_FOR_DURATION_META/@content').get() # Expect ISO 8601 like PT10M3S
        loader.add_value('duration_str', duration)

        uploader_ld = ld_data.get('author') or ld_data.get('channel')
        if isinstance(uploader_ld, dict):
            loader.add_value('uploader_name', uploader_ld.get('name'))
            loader.add_value('uploader_url', uploader_ld.get('url') or uploader_ld.get('@id'))
        else:
            loader.add_css('uploader_name', 'YOUR_SELECTOR_FOR_UPLOADER_NAME::text')
            loader.add_css('uploader_url', 'YOUR_SELECTOR_FOR_UPLOADER_LINK::attr(href)')

        tags_ld = ld_data.get('keywords') # Often comma-separated string or list
        if isinstance(tags_ld, str): tags_ld = [t.strip() for t in tags_ld.split(',')]
        loader.add_value('tags', tags_ld or response.css('YOUR_SELECTOR_FOR_TAGS a::text').getall())
        
        views = ld_data.get('interactionStatistic', {}).get('userInteractionCount') or response.xpath('YOUR_SELECTOR_FOR_VIEWS_META/@content').get() or response.css('YOUR_SELECTOR_FOR_VIEWS_DISPLAY::text').re_first(r'(\d[\d,\.]*)')
        loader.add_value('view_count_str', views)
        loader.add_css('like_count_str', 'YOUR_SELECTOR_FOR_LIKES_DISPLAY::text') # Often dynamic
        # dislike_count_str - similar to likes, often dynamic

        loader.add_value('language_code_video', ld_data.get('inLanguage') or response.xpath('//meta[@itemprop="inLanguage"]/@content').get())
        loader.add_value('licence_str', ld_data.get('license') or response.css('YOUR_SELECTOR_FOR_LICENSE_LINK::text').get()) # URL or text
        loader.add_value('category_str', ld_data.get('genre')) # Often 'genre' in ld+json
        # privacy_str - usually not publicly displayed directly, might be inferred or from API

        # VTT URL
        vtt_url_en = response.xpath('//video//track[@kind="captions" and (@srclang="en" or starts-with(@srclang, "en-"))][1]/@src').get()
        vtt_lang_en = "en" if vtt_url_en else None
        vtt_url_any = response.xpath('//video//track[@kind="captions"][1]/@src').get()
        vtt_lang_any = response.xpath('//video//track[@kind="captions"][1]/@srclang').get() if vtt_url_any else None
        
        final_vtt_url = vtt_url_en or vtt_url_any
        final_vtt_lang = vtt_lang_en or vtt_lang_any or 'und'
        if final_vtt_url:
            loader.add_value('transcript_vtt_url', response.urljoin(final_vtt_url))
            loader.add_value('language_code_caption', final_vtt_lang)
        
        loader.add_value('embed_url', ld_data.get('embedUrl') or response.xpath('//meta[@itemprop="embedURL"]/@content').get())
        loader.add_value('direct_video_url', ld_data.get('contentUrl') or response.xpath('//video/source[@type="video/mp4"][1]/@src').get() or response.xpath('//video[@src]/@src').get())
        
        loader.add_value('ld_json_data', json.dumps(ld_data) if ld_data else None)

        item = loader.load_item()
        if item.get('title') and item.get('original_url') and item.get('platform_video_id'):
            self.scraped_item_count += 1
            yield item
        else:
            logger.warning(f"Spider: Essential data missing for {response.url}. Title: {item.get('title')}, PlatformID: {item.get('platform_video_id')}. Item not yielded.")
