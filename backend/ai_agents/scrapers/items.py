# backend/ai_agents/scrapers/items.py
import scrapy

class PapriVideoItem(scrapy.Item):
    # Define the fields for your item here like:
    original_url = scrapy.Field()
    platform_name = scrapy.Field()
    platform_video_id = scrapy.Field()
    title = scrapy.Field()
    description = scrapy.Field()
    thumbnail_url = scrapy.Field()
    publication_date_str = scrapy.Field() # Will need parsing later
    duration_str = scrapy.Field()         # Will need parsing later
    uploader_name = scrapy.Field()
    uploader_url = scrapy.Field()
    tags = scrapy.Field() # list of strings
    view_count_str = scrapy.Field()       # Will need parsing
    like_count_str = scrapy.Field()       # Will need parsing
    transcript_text = scrapy.Field()      # If directly scraped
    transcript_vtt_url = scrapy.Field()   # URL to a VTT file
    language_code = scrapy.Field()        # Optional: language of the transcript if known
    embed_url = scrapy.Field()
    direct_video_url = scrapy.Field()     # Link to MP4/WebM if available
    # Add any other fields you aim to scrape
