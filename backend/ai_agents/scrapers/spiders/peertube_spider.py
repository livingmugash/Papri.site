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


class PeertubeSpider(scrapy.Spider):
    name = "peertube"
    # This would be parameterized or set dynamically by SOIAgent
    # start_urls = ['https://peertube.example.com/videos/trending'] # Example instance URL
    # allowed_domains = ['peertube.example.com']

    def __init__(self, start_url=None, *args, **kwargs):
        super(PeertubeSpider, self).__init__(*args, **kwargs)
        if start_url:
            self.start_urls = [start_url]
            self.allowed_domains = [urlparse(start_url).netloc]
        else:
            # Default or raise error if no start_url provided
            # For testing, you can hardcode one
            # self.start_urls = ['https://your-target-peertube-instance.com/videos/local']
            # self.allowed_domains = ['your-target-peertube-instance.com']
            print("PeertubeSpider: No start_url provided!")
            self.start_urls = [] 


    def parse(self, response):
        """
        Parses video listing pages to find links to individual video pages.
        This uses generic CSS selectors; actual selectors will vary GREATLY per PeerTube instance theme.
        """
        self.logger.info(f"PeertubeSpider: Parsing listing page: {response.url}")
        
        # Example selectors - THESE WILL NEED TO BE INSPECTED AND ADJUSTED PER TARGET SITE
        video_links = response.css('div.video-miniature a. ভিডিও-link-miniature::attr(href)').getall()
        # A more robust selector might be needed, e.g., one that targets the container of each video item
        # and then extracts the link from within.

        for video_href in video_links:
            full_video_url = response.urljoin(video_href)
            yield scrapy.Request(full_video_url, callback=self.parse_video_page)

        # Example for pagination -  THIS IS HIGHLY SITE-SPECIFIC
        # next_page = response.css('a.pagination-next::attr(href)').get()
        # if next_page:
        #     yield response.follow(next_page, callback=self.parse)


    def parse_video_page(self, response):
        """
        Parses an individual video page to extract all relevant metadata.
        Selectors are EXAMPLES and WILL VARY.
        """
        self.logger.info(f"PeertubeSpider: Parsing video page: {response.url}")
        
        loader = ItemLoader(item=PapriVideoItem(), response=response)

        loader.add_value('original_url', response.url)
        loader.add_value('platform_name', 'PeerTube') # Or more specific instance name

        # Example: Extracting video ID from URL (e.g., /w/xxxxxxxxxxxxx)
        video_id_match = response.url.split('/w/')[-1]
        if video_id_match:
             loader.add_value('platform_video_id', video_id_match.split('?')[0]) # Remove query params

        # THESE SELECTORS ARE EXAMPLES - MUST BE ADJUSTED FOR THE TARGET PEERTUBE INSTANCE'S THEME
        loader.add_css('title', 'h1.video-title::text') # Common for title
        loader.add_css('description', 'div.video-description-markdown p::text') # Could be more complex
        
        # Thumbnails might be in a <meta property="og:image"> tag or an <img> tag
        loader.add_xpath('thumbnail_url', '//meta[@property="og:image"]/@content')
        
        # Publication date might be in a <meta> tag or a time element
        # loader.add_css('publication_date_str', 'span.date-label time::attr(datetime)')
        # Or from <script type="application/ld+json"> if present
        
        # Duration often in player or meta tags
        # loader.add_xpath('duration_str', '//meta[@itemprop="duration"]/@content') # e.g., PT10M32S

        # Uploader info
        # loader.add_css('uploader_name', 'div.video-channel-name a::text')
        # loader.add_css('uploader_url', 'div.video-channel-name a::attr(href)')
        
        # Tags
        # loader.add_css('tags', 'div.video-tags a.tag::text')

        # View count, likes - these are often dynamically loaded or tricky
        # loader.add_css('view_count_str', 'span.views-label ::text')

        # Captions/Transcripts (VTT files) - check network tab or page source for how they are linked
        # loader.add_xpath('transcript_vtt_url', '//track[@kind="captions"]/@src')

        # Embed URL or direct video file (might be in <video> tag or player config JS)
        # loader.add_css('embed_url', 'meta[itemprop="embedUrl"]::attr(content)')
        # loader.add_css('direct_video_url', 'video#मेरा-वीडियो-प्लेयर source[type="video/mp4"]::attr(src)')

        # --- Log what selectors found (for debugging) ---
        # title_found = response.css('h1.video-title::text').get()
        # self.logger.info(f"Title found by selector: {title_found}")
        # --- End log ---

        yield loader.load_item()
