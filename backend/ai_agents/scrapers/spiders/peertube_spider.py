# backend/ai_agents/scrapers/spiders/peertube_spider.py
import scrapy
from scrapy.loader import ItemLoader
from urllib.parse import urlparse, urljoin
import json
import re
import logging
from ..items import PapriVideoItem

logger = logging.getLogger(__name__)

class PeertubeSpider(scrapy.Spider):
    name = "peertube"
    custom_settings = { # Overrides from scrapers/settings.py 
        'DOWNLOAD_DELAY': 2.0,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2, # Be respectful
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
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

    def parse_ld_json_data(self, response): # 
        ld_json_scripts = response.xpath('//script[@type="application/ld+json"]/text()').getall()
        for script_content in ld_json_scripts:
            try:
                data = json.loads(script_content)
                # PeerTube often has VideoObject in the main object or within a list (e.g., ItemList)
                if isinstance(data, list): 
                    data = next((item for item in data if isinstance(item, dict) and item.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']), None)
                if isinstance(data, dict) and data.get('@type') in ['VideoObject', 'Clip', 'TVEpisode']:
                    logger.debug(f"LD+JSON VideoObject found on {response.url}")
                    return data
            except Exception: pass # Ignore parsing errors for individual scripts
        return {} # Return empty dict if not found

    def parse(self, response): # For listing pages 
        if not self.start_urls or self.scraped_item_count >= self.max_items: return
        logger.info(f"PeertubeSpider: Parsing listing: {response.url}. Scraped: {self.scraped_item_count}/{self.max_items}")

        # === [YOU] YOUR_SELECTOR_HERE for video links on listing pages ===
        # Example: based on common PeerTube themes; these are highly variable
        # Use multiple selectors as fallbacks.
        # PDF implies data like `name`, `thumbnailPath`, `channel.displayName` is available. 
        video_links = response.css('YOUR_SELECTOR_FOR_VIDEO_LINK_IN_LISTING_ITEM::attr(href)').getall()
        # if not video_links: video_links = response.xpath('YOUR_XPATH_SELECTOR_FOR_VIDEO_LINK::attr(href)').getall()
        
        logger.debug(f"Found {len(video_links)} potential video links on {response.url}")
        for href in video_links:
            if self.scraped_item_count >= self.max_items:
                logger.info(f"Max items ({self.max_items}) reached from listing. Stopping."); return
            full_video_url = response.urljoin(href)
            if '/w/' in full_video_url or '/videos/watch/' in full_video_url: # PeerTube patterns
                yield scrapy.Request(full_video_url, callback=self.parse_video_page)
        
        # === [YOU] YOUR_SELECTOR_HERE for pagination ===
        # next_page = response.css('YOUR_SELECTOR_FOR_NEXT_PAGE_LINK::attr(href)').get()
        # if next_page and self.scraped_item_count < self.max_items:
        #     yield response.follow(next_page, callback=self.parse)

    def parse_video_page(self, response): # 
        if self.scraped_item_count >= self.max_items: return
        logger.info(f"PeertubeSpider: Parsing video page: {response.url}")
        
        ld_data = self.parse_ld_json_data(response)
        loader = ItemLoader(item=PapriVideoItem(), response=response) # 

        loader.add_value('original_url', response.url)
        loader.add_value('instance_url', f"{response.urlparts.scheme}://{response.urlparts.netloc}")
        loader.add_value('platform_name', f'PeerTube_{response.urlparts.netloc}')

        # Video ID - from PDF: Video.uuid (usually part of URL) 
        # ... (video_id extraction logic from Step 36 is good) ...
        url_path = response.urlparts.path; video_id = None
        match_uuid = re.search(r'/(?:videos/watch/|videos/embed/|w/)(?P<id>[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})', url_path)
        if match_uuid: video_id = match_uuid.group('id')
        else:
            match_short_id = re.search(r'/w/(?P<id>[a-zA-Z0-9_-]+)', url_path)
            if match_short_id: video_id = match_short_id.group('id')
        if not video_id: video_id = ld_data.get('identifier') or response.xpath('//meta[@itemprop="identifier"]/@content').get()
        loader.add_value('platform_video_id', video_id)

        # === [YOU] ADD/VERIFY YOUR SELECTORS FOR EACH FIELD BELOW ===
        # Prioritize LD+JSON, then meta tags, then specific CSS/XPath from page structure.
        # Fields based on your PDF (Table 1: PeerTube Data Attributes vs. PapriVideoltem Fields) 
        # and Section 4 (Detailed Analysis) 

        loader.add_value('title', ld_data.get('name') or response.xpath('//meta[@property="og:title"]/@content').get() or response.css('YOUR_SELECTOR_FOR_H1_TITLE::text').get())
        loader.add_value('description', ld_data.get('description') or response.xpath('//meta[@property="og:description"]/@content').get() or response.css('YOUR_SELECTOR_FOR_DESCRIPTION ::text').getall())
        loader.add_value('thumbnail_url', ld_data.get('thumbnailUrl') or response.xpath('//meta[@property="og:image"]/@content').get() or response.css('YOUR_SELECTOR_FOR_VIDEO_THUMBNAIL_IMG::attr(src)').get())
        
        pub_date = ld_data.get('uploadDate') or ld_data.get('datePublished') or response.xpath('//meta[@itemprop="uploadDate"]/@content').get() or response.css('YOUR_SELECTOR_FOR_PUBLICATION_DATE::attr(datetime)').get() or response.css('YOUR_SELECTOR_FOR_PUBLICATION_DATE_TEXT::text').get()
        loader.add_value('publication_date_str', pub_date)
        
        duration = ld_data.get('duration') or response.xpath('//meta[@itemprop="duration"]/@content').get() # Expect ISO 8601 PTxMxS
        loader.add_value('duration_str', duration)

        uploader_ld = ld_data.get('author') or ld_data.get('channel') # 
        if isinstance(uploader_ld, dict):
            loader.add_value('uploader_name', uploader_ld.get('name'))
            loader.add_value('uploader_url', response.urljoin(uploader_ld.get('url') or uploader_ld.get('@id','')))
        else:
            loader.add_css('uploader_name', 'YOUR_SELECTOR_FOR_UPLOADER_NAME_TEXT::text')
            loader.add_css('uploader_url', 'YOUR_SELECTOR_FOR_UPLOADER_PROFILE_LINK::attr(href)')

        tags_ld = ld_data.get('keywords'); tags_page = response.css('YOUR_SELECTOR_FOR_TAGS_LIST a::text').getall()
        if isinstance(tags_ld, str): tags_ld = [t.strip() for t in tags_ld.split(',')]
        loader.add_value('tags', tags_ld or tags_page) # 
        
        views = ld_data.get('interactionStatistic', {}).get('userInteractionCount') or response.xpath('//meta[@itemprop="interactionCount"]/@content').get() or response.css('YOUR_SELECTOR_FOR_VIEWS_TEXT::text').re_first(r'(\d[\d,\.]*)')
        loader.add_value('view_count_str', views) # 
        loader.add_css('like_count_str', 'YOUR_SELECTOR_FOR_LIKES_TEXT::text') # 
        # loader.add_css('dislike_count_str', 'YOUR_SELECTOR_FOR_DISLIKES_TEXT::text') # 

        loader.add_value('language_code_video', ld_data.get('inLanguage') or response.xpath('//meta[@itemprop="inLanguage"]/@content').get()) # 
        loader.add_value('licence_str', ld_data.get('license') or response.css('YOUR_SELECTOR_FOR_LICENSE_TEXT_OR_LINK_TEXT::text').get()) # 
        loader.add_value('category_str', ld_data.get('genre') or response.css('YOUR_SELECTOR_FOR_CATEGORY_TEXT::text').get()) # 
        loader.add_value('privacy_str', ld_data.get('isAccessibleForFree') == False and 'private' or ld_data.get('isAccessibleForFree') and 'public') # Infer from ld+json; direct privacy often not on page 

        # Transcript/Caption VTT URL & Language 
        vtt_tracks = response.xpath('//video//track[@kind="captions"]')
        # Prioritize English, then first available
        chosen_vtt_url, chosen_vtt_lang = None, 'und'
        for track in vtt_tracks:
            src = track.xpath('./@src').get()
            srclang = track.xpath('./@srclang').get()
            if src:
                if not chosen_vtt_url: # Take first one
                    chosen_vtt_url = response.urljoin(src)
                    if srclang: chosen_vtt_lang = srclang
                if srclang and ('en' in srclang.lower()): # Prioritize English
                    chosen_vtt_url = response.urljoin(src)
                    chosen_vtt_lang = srclang
                    break 
        if chosen_vtt_url:
            loader.add_value('transcript_vtt_url', chosen_vtt_url)
            loader.add_value('language_code_caption', chosen_vtt_lang)
        
        loader.add_value('embed_url', ld_data.get('embedUrl') or response.xpath('//meta[@itemprop="embedURL"]/@content').get()) # 
        loader.add_value('direct_video_url', ld_data.get('contentUrl') or response.xpath('//video/source[@type="video/mp4"][1]/@src').get() or response.xpath('//video[@src]/@src').get()) # 
        
        # Store first ld+json block if it exists
        ld_json_content = response.xpath('//script[@type="application/ld+json"]/text()').get()
        if ld_json_content:
            try: loader.add_value('ld_json_data', json.dumps(json.loads(ld_json_content))) # Store as string
            except: pass


        item = loader.load_item()
        if item.get('title') and item.get('original_url') and item.get('platform_video_id'):
            self.scraped_item_count += 1
            yield item
        else:
            logger.warning(f"PeertubeSpider: Essential data missing for {response.url}. Title:'{item.get('title')}', ID:'{item.get('platform_video_id')}'. Item NOT yielded.")
