# backend/ai_agents/source_orchestration_agent.py
import subprocess
import json
import tempfile
from urllib.parse import urlparse, urljoin, quote # Added quote
import os
import shutil
import logging
import requests # Keep for API calls if needed, and for quote
from django.conf import settings
from django.utils import timezone # For date parsing
from dateutil import parser as dateutil_parser # For robust date parsing: pip install python-dateutil

logger = logging.getLogger(__name__)

class SourceOrchestrationAgent:
    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.vimeo_access_token = settings.VIMEO_ACCESS_TOKEN
        self.scrapy_executable = shutil.which('scrapy')
        if not self.scrapy_executable:
            logger.error("SOIAgent: Scrapy executable not found in PATH. Scraping will be disabled.")
        self.scrapers_base_dir = os.path.join(settings.BASE_DIR, 'ai_agents', 'scrapers')
        # Ensure a minimal scrapy.cfg exists in self.scrapers_base_dir for Scrapy to recognize it as project root.
        # Content of backend/ai_agents/scrapers/scrapy.cfg:
        # [settings]
        # default = settings # Tells Scrapy to look for scrapers/settings.py
        if not os.path.exists(os.path.join(self.scrapers_base_dir, 'scrapy.cfg')):
             logger.warning(f"SOIAgent: scrapy.cfg not found in {self.scrapers_base_dir}. Subprocess CWD might be an issue.")


    def _run_scrapy_spider(self, spider_name, start_url_for_spider, target_domain_for_spider, output_file_path, max_items_scraped, search_query_for_spider=None):
        if not self.scrapy_executable:
            logger.error("SOIAgent: Scrapy executable not available.")
            return False
        
        command = [
            self.scrapy_executable, 'crawl', spider_name,
            '-a', f'start_url={start_url_for_spider}',
            '-a', f'target_domain={target_domain_for_spider}',
            '-a', f'max_items_to_scrape={max_items_scraped}',
            '-o', output_file_path,
            '-s', 'LOG_LEVEL=INFO',
            # Provide path to settings.py relative to CWD (scrapers_base_dir)
            # This is one way to ensure Scrapy finds your project settings if needed.
            # However, a scrapy.cfg in scrapers_base_dir defining settings module is cleaner.
            # '-s', 'SETTINGS_MODULE=settings' # Assuming settings.py is in scrapers_base_dir
        ]
        if search_query_for_spider:
            command.extend(['-a', f'search_query={search_query_for_spider}'])
        
        logger.info(f"SOIAgent: Running Scrapy from CWD '{self.scrapers_base_dir}': {' '.join(command)}")
        
        # Prepare environment to help Scrapy find modules if needed
        env = os.environ.copy()
        # Add parent of scrapers_base_dir (ai_agents) and backend dir itself to PYTHONPATH
        # This allows imports like `from ..items import PapriVideoItem` in spider,
        # and Django model imports if spider needs them (though generally avoid).
        backend_dir = settings.BASE_DIR 
        ai_agents_dir = os.path.dirname(self.scrapers_base_dir) # should be backend/ai_agents
        current_pythonpath = env.get('PYTHONPATH', '')
        env['PYTHONPATH'] = f"{backend_dir}{os.pathsep}{ai_agents_dir}{os.pathsep}{current_pythonpath}"

        try:
            process = subprocess.run(command, cwd=self.scrapers_base_dir, capture_output=True, 
                                   text=True, check=False, timeout=300, encoding='utf-8', 
                                   errors='ignore', env=env)
            if process.returncode != 0:
                logger.error(f"SOIAgent: Scrapy '{spider_name}' failed for {start_url_for_spider}. Code: {process.returncode}.\nStderr: {process.stderr[-1000:]}\nStdout: {process.stdout[-1000:]}")
                return False
            logger.info(f"SOIAgent: Scrapy '{spider_name}' completed for {start_url_for_spider}. Output: {output_file_path}")
            return True
        except subprocess.TimeoutExpired: # ...
            logger.error(f"SOIAgent: Scrapy '{spider_name}' timed out for {start_url_for_spider}.")
            return False
        except Exception as e: # ...
            logger.error(f"SOIAgent: Exception running Scrapy '{spider_name}' for {start_url_for_spider}: {e}", exc_info=True)
            return False

    def _parse_duration_str_to_seconds(self, duration_str): # Renamed and enhanced
        if not duration_str: return None
        import re
        duration_str_upper = str(duration_str).upper()
        
        # Check for ISO 8601 Duration format (e.g., PT1H2M30S)
        if duration_str_upper.startswith("PT"):
            h, m, s = 0, 0, 0
            h_match = re.search(r'(\d+)H', duration_str_upper); h = int(h_match.group(1)) if h_match else 0
            m_match = re.search(r'(\d+)M', duration_str_upper); m = int(m_match.group(1)) if m_match else 0
            s_match = re.search(r'(\d+)S', duration_str_upper); s = int(s_match.group(1)) if s_match else 0
            if h or m or s: return h * 3600 + m * 60 + s
        
        # Check for HH:MM:SS, MM:SS, or SS format
        parts = []
        for p_str in str(duration_str).split(':'):
            try: parts.append(int(float(p_str))) # Allow float then int for safety
            except ValueError: return None # Invalid part

        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        if len(parts) == 1: return parts[0] # Assume seconds if single number
        
        logger.warning(f"SOIAgent: Could not parse duration string: '{duration_str}'")
        return None

    def _parse_datetime_str_to_iso(self, date_str): # Renamed and enhanced
        if not date_str: return None
        try:
            dt_obj = dateutil_parser.parse(date_str)
            # Convert to UTC and then to ISO format string
            if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None: # If naive
                dt_obj = timezone.make_aware(dt_obj, timezone.get_default_timezone()) # Assume Django's default TZ
            return dt_obj.astimezone(timezone.utc).isoformat() # Return ISO string
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"SOIAgent: Could not parse date string '{date_str}': {e}")
            return None

    def search_scraped_platform(self, platform_config, query_text_original, max_items_per_scrape=5):
        # ... (spider_name, base_url, target_domain setup as before) ...
        spider_name = platform_config['spider_name']
        base_url = platform_config['base_url']
        target_domain = urlparse(base_url).netloc
        search_query_for_spider = query_text_original # Pass original query to spider if it uses it

        start_url_for_spider = platform_config.get('default_listing_url', base_url) # Fallback
        if platform_config.get('search_path_template') and query_text_original:
            try:
                search_path = platform_config['search_path_template'].format(query=quote(query_text_original))
                start_url_for_spider = urljoin(base_url.rstrip('/') + '/', search_path.lstrip('/')) # Robust URL joining
            except Exception as e:
                 logger.error(f"SOIAgent: Error formatting search path for {platform_config['name']}: {e}. Using default listing.")
        
        logger.info(f"SOIAgent: Scraping {platform_config['name']} via '{spider_name}', Start: {start_url_for_spider}")
        
        scraped_items_converted = []
        temp_scrapy_dir = os.path.join(settings.MEDIA_ROOT, "temp_scrapy_outputs"); os.makedirs(temp_scrapy_dir, exist_ok=True)

        # Use a unique filename for each scrape job
        tmp_file_name = f"{spider_name}_{target_domain}_{timezone.now().strftime('%Y%m%d%H%M%S')}.json"
        tmp_output_file_path = os.path.join(temp_scrapy_dir, tmp_file_name)
        
        if self._run_scrapy_spider(spider_name, start_url_for_spider, target_domain, tmp_output_file_path, max_items_per_scrape, search_query_for_spider):
            try:
                with open(tmp_output_file_path, 'r', encoding='utf-8') as f:
                    raw_scraped_data = json.load(f)
                
                if isinstance(raw_scraped_data, list):
                    for item in raw_scraped_data:
                        # More careful conversion and adding instance_url if spider doesn't
                        platform_name_from_item = item.get('platform_name', f'PeerTube_{target_domain}')
                        if not item.get('instance_url') and target_domain:
                            item['instance_url'] = f"https://{target_domain}" # Assuming https

                        converted = {
                            'platform_name': platform_name_from_item,
                            'platform_video_id': item.get('platform_video_id'), # Spider MUST provide this
                            'title': item.get('title'),
                            'description': " ".join(item.get('description', [])) if isinstance(item.get('description'), list) else item.get('description'), # Join if list from getall()
                            'thumbnail_url': item.get('thumbnail_url'),
                            'publication_date': self._parse_datetime_str_to_iso(item.get('publication_date_str')),
                            'duration_seconds': self._parse_duration_str_to_seconds(item.get('duration_str')),
                            'original_url': item.get('original_url'), # Spider MUST provide this
                            'embed_url': item.get('embed_url') or item.get('direct_video_url'),
                            'uploader_name': item.get('uploader_name'),
                            'tags': item.get('tags', []),
                            'view_count': int(str(item.get('view_count_str','0')).replace(',','').split(' ')[0]) if item.get('view_count_str','0').replace(',','').split(' ')[0].isdigit() else 0,
                            'like_count': int(str(item.get('like_count_str','0')).replace(',','').split(' ')[0]) if item.get('like_count_str','0').replace(',','').split(' ')[0].isdigit() else 0,
                            'language_code_video': item.get('language_code_video'),
                            'licence_str': item.get('licence_str'),
                            'category_str': item.get('category_str'),
                            'privacy_str': item.get('privacy_str'),
                            'transcript_vtt_url': item.get('transcript_vtt_url'), # Crucial for CAAgent
                            'language_code_caption': item.get('language_code_caption'), # Crucial for CAAgent
                            'raw_item_data_for_debug': item if settings.DEBUG else None # Store raw for debugging
                        }
                        if converted['original_url'] and converted['title'] and converted['platform_video_id']:
                            scraped_items_converted.append(converted)
                        # else: logger.warning(f"SOIAgent: Skipped scraped item due to missing essential fields: {item.get('title')}, {item.get('original_url')}")
                else: logger.warning(f"SOIAgent: Scrapy output {tmp_output_file_path} not a list.")
            except json.JSONDecodeError: logger.error(f"SOIAgent: Failed to decode JSON: {tmp_output_file_path}")
            except Exception as e: logger.error(f"SOIAgent: Error processing Scrapy output for {platform_config['name']}: {e}", exc_info=True)
            # finally: # Keep temp files for debugging if DEBUG is True
            #     if not settings.DEBUG and os.path.exists(tmp_output_file_path): os.remove(tmp_output_file_path)
        else: # Spider run failed
             if os.path.exists(tmp_output_file_path): os.remove(tmp_output_file_path) # Still cleanup

        logger.info(f"SOIAgent: {platform_config['name']} scraping yielded {len(scraped_items_converted)} converted items.")
        return scraped_items_converted

    def fetch_content_from_sources(self, processed_query_data):
        # ... (API calls as before) ...
        all_source_results = []; query_text_for_apis = processed_query_data.get('processed_query', ''); query_original_text = processed_query_data.get('original_query', '')
        if query_text_for_apis:
            all_source_results.extend(self.search_youtube(query_text_for_apis, max_results=5)) # Reduced max_results for faster V1 test
            all_source_results.extend(self.search_vimeo(query_text_for_apis, max_results=5))
            all_source_results.extend(self.search_dailymotion(query_text_for_apis, max_results=5))

        # Scraped Sources - YOU NEED TO CONFIGURE THIS `scrapeable_platforms` list
        # with the actual instances and search paths/listing paths you want to target.
        scrapeable_platforms = [] 
        # Example (replace with your actual target for testing):
        # scrapeable_platforms = [
        #     {
        #         'name': 'PeerTube_Tilvids_Test', 'spider_name': 'peertube', 
        #         'base_url': 'https://tilvids.com', # YOUR CHOSEN INSTANCE
        #         'search_path_template': '/search/videos?search={query}&searchTarget=local', 
        #         'default_listing_url': 'https://tilvids.com/videos/recently-added'
        #     }
        # ]
        if scrapeable_platforms and query_original_text and processed_query_data.get('intent') in ['general_video_search', 'hybrid_text_visual_search']:
            for platform_config in scrapeable_platforms:
                scraped_data = self.search_scraped_platform(platform_config, query_original_text, max_items_per_scrape=3) # Scrape few items for testing
                all_source_results.extend(scraped_data)
        
        logger.info(f"SOIAgent: Total from ALL sources: {len(all_source_results)}")
        return all_source_results

    # API Search methods (search_youtube, search_vimeo, search_dailymotion) from Step 12 are assumed to be here and functional.
    # Make sure they are robust and log errors.

# In _run_scrapy_spider method
env = os.environ.copy()
# Add parent of scrapers_base_dir to PYTHONPATH for the subprocess
# so 'from ..items import PapriVideoItem' can work if items.py is in 'scrapers'
# and spiders are in 'scrapers/spiders'
python_path_addition = os.path.dirname(self.scrapers_base_dir) # This would be 'backend/ai_agents'
env['PYTHONPATH'] = f"{python_path_addition}{os.pathsep}{env.get('PYTHONPATH', '')}"

process = subprocess.run(command, cwd=self.scrapers_base_dir, capture_output=True, 
                         text=True, check=False, timeout=300, encoding='utf-8', 
                         errors='ignore', env=env) # Pass modified env

