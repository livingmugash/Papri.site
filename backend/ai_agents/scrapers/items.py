# backend/ai_agents/scrapers/items.py
import scrapy

class PapriVideoItem(scrapy.Item):
    # Core identification
    original_url = scrapy.Field()         # From response.url, PDF implied 
    platform_name = scrapy.Field()      # e.g., "PeerTube_instance.name" 
    platform_video_id = scrapy.Field()  # Derived from URL or ld+json, PDF: Video.uuid 
    
    # Essential Metadata from PDF (PeerTube Video attributes)
    title = scrapy.Field()                # PDF: name 
    description = scrapy.Field()          # PDF: description 
    thumbnail_url = scrapy.Field()        # PDF: thumbnailPath (as URL) 
    publication_date_str = scrapy.Field() # PDF: originallyPublishedAt (raw string) 
    duration_str = scrapy.Field()         # PDF: duration (raw string or seconds) 
    
    # Extended Metadata from PDF
    uploader_name = scrapy.Field()        # PDF: Video.channel -> Channel.displayName 
    uploader_url = scrapy.Field()         # PDF: Video.channel -> Channel.url (or derived) 
    tags = scrapy.Field()                 # PDF: tags (list of strings) 
    view_count_str = scrapy.Field()       # PDF: views (raw string) 
    like_count_str = scrapy.Field()       # PDF: likes (raw string) 
    dislike_count_str = scrapy.Field()    # PDF: dislikes (raw string) 
    
    language_code_video = scrapy.Field()  # PDF: language (language of the video content itself) 
    licence_str = scrapy.Field()          # PDF: licence (string identifier) 
    category_str = scrapy.Field()         # PDF: category (string identifier) 
    privacy_str = scrapy.Field()          # PDF: privacy (string e.g., "Public") 
    
    instance_url = scrapy.Field()         # PDF: instance_url (Base URL of the PeerTube instance) 
    
    # Transcript/Caption Info from PDF (PeerTube VideoCaption attributes)
    transcript_vtt_url = scrapy.Field()   # PDF: captionPath (URL to VTT/SRT) 
    language_code_caption = scrapy.Field()# PDF: language (of caption file) 
    
    # Playback Info
    embed_url = scrapy.Field()            # PDF: embedPath (as URL) 
    direct_video_url = scrapy.Field()     # PDF: fileDownloadUrl (from /source endpoint) or similar 

    ld_json_data = scrapy.Field()         # Store content of <script type="application/ld+json"> 

    def __repr__(self):
        return f"<PapriVideoItem title='{self.get('title', 'N/A')[:30]}' url='{self.get('original_url', 'N/A')}'>"
