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
    # PeerTube Attribute: language -> Field: language (e.g., 'en', 'fr')
    language_code_video = scrapy.Field()  # Language of the video itself, distinct from caption language
    
    # PeerTube Attribute: licence -> Field: licence (integer or string identifier)
    licence_str = scrapy.Field()          # e.g., "Attribution", "Public Domain" or its ID
    
    # PeerTube Attribute: category -> Field: category (integer or string identifier)
    category_str = scrapy.Field()         # e.g., "Music", "Education" or its ID
    
    # PeerTube Attribute: privacy -> Field: privacy (integer or string identifier: Public, Unlisted, Private, Internal)
    privacy_str = scrapy.Field()
    
    # PeerTube Attribute: duration -> Field: duration (seconds)
    duration_str = scrapy.Field()         # Raw duration string from site (e.g., "PT10M32S", "10:32")
    
    # PeerTube Attribute: originallyPublishedAt -> Field: originally_published_at
    publication_date_str = scrapy.Field() # Raw date string from site (ISO 8601 or other)
    
    # PeerTube Attribute: views -> Field: views
    view_count_str = scrapy.Field()       # Raw view count string
    
    # PeerTube Attribute: likes -> Field: likes
    like_count_str = scrapy.Field()
    
    # PeerTube Attribute: dislikes -> Field: dislikes
    dislike_count_str = scrapy.Field()
    
    # PeerTube Attribute: channel -> Field: channel (ForeignKey to Channel model)
    # For scraping, we'll get channel name and URL
    channel_name_on_platform = scrapy.Field() # Extracted uploader/channel name
    channel_url_on_platform = scrapy.Field()  # URL to the channel page on the instance

    # PeerTube Attribute: thumbnailPath -> Field: thumbnail_url
    thumbnail_url = scrapy.Field()        # Full URL to the thumbnail
    
    # PeerTube Attribute: embedPath / embedUrl -> Field: embed_url
    embed_url = scrapy.Field()            # Full URL for embedding
    
    # Custom field: Instance URL where this video was found
    instance_url = scrapy.Field()         # Base URL of the PeerTube instance
    
    # Custom field: Platform name (e.g., PeerTube_tilvids.com)
    platform_name = scrapy.Field()
    
    # Custom field: Extracted platform specific video ID
    platform_video_id = scrapy.Field()

    # --- From PDF: Caption Entity ---
    # Related to a Video. Each caption has a language and a file URL (or content).
    # The spider will aim to find the VTT URL and its language.
    # PeerTube Attribute: captionPath (file URL), language -> Fields: transcript_vtt_url, language_code_caption
    
    transcript_vtt_url = scrapy.Field()   # Full URL to a VTT caption file
    language_code_caption = scrapy.Field()# Language of this specific caption file (e.g., 'en', 'es')
                                          # Spider might find multiple VTTs for different languages.
                                          # For simplicity, SOIAgent might pick one or process based on priorities.

    # --- From PDF: Channel Entity (related, but primarily for context if scraping channel pages) ---
    # For video items, we primarily care about the channel info linked to the video (uploader_name, uploader_url).
    # The fields 'channel_name_on_platform' and 'channel_url_on_platform' cover this for the video item.

    # Direct video file (if scraper can find it)
    direct_video_url = scrapy.Field()     # Link to MP4/WebM if available

    # Store the raw LD+JSON script content if found, as it often contains rich metadata
    ld_json_data = scrapy.Field()

    # To help with deduplication if a stable content hash is extractable or known
    # content_hash_from_source = scrapy.Field()


