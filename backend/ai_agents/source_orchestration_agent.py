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
        # ... (API keys, scrapy_executable, scrapers_base_dir, minimal scrapy.cfg creation as in Step 36) ...
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.vimeo_access_token = settings.VIMEO_ACCESS_TOKEN
        self.scrapy_executable = shutil.which('scrapy')
        if not self.scrapy_executable: logger.error("SOIAgent: Scrapy executable not found. Scraping disabled.")
        self.scrapers_base_dir = os.path.join(settings.BASE_DIR, 'ai_agents', 'scrapers')
        cfg_path = os.path.join(self.scrapers_base_dir, 'scrapy.cfg')
        if not os.path.exists(cfg_path):
             try:
                 with open(cfg_path, 'w') as f: f.write("[settings]\ndefault = settings\n") # Assumes scrapers/settings.py
                 logger.info(f"SOIAgent: Created minimal scrapy.cfg at {cfg_path}")
             except IOError as e: logger.error(f"SOIAgent: Could not create scrapy.cfg at {cfg_path}: {e}")


    def _run_scrapy_spider(self, spider_name, start_url_for_spider, target_domain_for_spider, output_file_path, max_items_scraped, search_query_for_spider=None):
        # ... (Implementation from Step 36, ensure robust error logging and env for PYTHONPATH) ...
        if not self.scrapy_executable: return False
        command = [self.scrapy_executable, 'crawl', spider_name, '-a', f'start_url={start_url_for_spider}', 
                   '-a', f'target_domain={target_domain_for_spider}', '-a', f'max_items_to_scrape={max_items_scraped}',
                   '-o', output_file_path, '-s', 'LOG_LEVEL=INFO'] # LOG_LEVEL from spider/project settings
        if search_query_for_spider: command.extend(['-a', f'search_query={search_query_for_spider}'])
        logger.info(f"SOIAgent: Running Scrapy from CWD '{self.scrapers_base_dir}': {' '.join(command)}")
        env = os.environ.copy(); backend_dir = settings.BASE_DIR; ai_agents_dir = os.path.dirname(self.scrapers_base_dir)
        env['PYTHONPATH'] = f"{backend_dir}{os.pathsep}{ai_agents_dir}{os.pathsep}{env.get('PYTHONPATH', '')}"
        try:
            process = subprocess.run(command, cwd=self.scrapers_base_dir, capture_output=True, text=True, check=False, timeout=450, encoding='utf-8', errors='ignore', env=env) # Increased timeout
            if process.returncode != 0: logger.error(f"SOIAgent: Scrapy '{spider_name}' FAILED for {start_url_for_spider}. Code: {process.returncode}.\nStderr: {process.stderr[-1000:]}\nStdout: {process.stdout[-1000:]}"); return False
            logger.info(f"SOIAgent: Scrapy '{spider_name}' COMPLETED for {start_url_for_spider}. Output: {output_file_path}")
            return True
        except subprocess.TimeoutExpired: logger.error(f"SOIAgent: Scrapy '{spider_name}' TIMED OUT for {start_url_for_spider}."); return False
        except Exception as e: logger.error(f"SOIAgent: EXCEPTION running Scrapy '{spider_name}' for {start_url_for_spider}: {e}", exc_info=True); return False

    def _parse_duration_str_to_seconds(self, duration_str): # 
        # ... (Implementation from Step 36 - robust ISO 8601 and HH:MM:SS parsing) ...
        if not duration_str: return None; duration_str_upper = str(duration_str).upper()
        if duration_str_upper.startswith("PT"): h,m,s=0,0,0; h_match=re.search(r'(\d+)H',duration_str_upper);h=int(h_match.group(1))if h_match else 0;m_match=re.search(r'(\d+)M',duration_str_upper);m=int(m_match.group(1))if m_match else 0;s_match=re.search(r'(\d+)S',duration_str_upper);s=int(s_match.group(1))if s_match else 0; total_seconds = h*3600+m*60+s; return total_seconds if total_seconds > 0 else None
        else: parts=[int(p) for p in str(duration_str).split(':') if p.isdigit()];_l=len(parts); return parts[0]*3600+parts[1]*60+parts[2] if _l==3 else (parts[0]*60+parts[1] if _l==2 else (parts[0] if _l==1 else None))
        return None
        
    def _parse_datetime_str_to_iso(self, date_str): # 
        if not date_str: return None
        try:
            dt_obj = dateutil_parser.parse(date_str) # Robust parsing
            if dt_obj.tzinfo is None or dt_obj.tzinfo.utcoffset(dt_obj) is None: dt_obj = timezone.make_aware(dt_obj, timezone.get_default_timezone())
            return dt_obj.astimezone(timezone.utc).isoformat() # Return ISO string with Z
        except (ValueError, TypeError, OverflowError) as e: logger.warning(f"SOIAgent: Could not parse date string '{date_str}': {e}"); return None

    def search_scraped_platform(self, platform_config, query_text_original, max_items_per_scrape=5): # 
        spider_name = platform_config['spider_name']; base_url = platform_config['base_url']; target_domain = urlparse(base_url).netloc
        search_query_for_spider = query_text_original # Spider can use this if it hits a search endpoint

        start_url_for_spider = platform_config.get('default_listing_url', base_url)
        if platform_config.get('search_path_template') and query_text_original:
            try: start_url_for_spider = urljoin(base_url.rstrip('/') + '/', platform_config['search_path_template'].format(query=quote(query_text_original)).lstrip('/'))
            except Exception as e: logger.error(f"SOIAgent: Error formatting search path for {platform_config['name']}: {e}. Using default.")
        
        logger.info(f"SOIAgent: Scraping {platform_config['name']} via '{spider_name}', StartURL: {start_url_for_spider}, Query: '{search_query_for_spider}'")
        
        converted_items = []; temp_scrapy_dir = os.path.join(settings.MEDIA_ROOT, "temp_scrapy_outputs"); os.makedirs(temp_scrapy_dir, exist_ok=True)
        tmp_file_name = f"{spider_name}_{target_domain}_{timezone.now().strftime('%Y%m%d%H%M%S%f')}.json"
        tmp_output_file_path = os.path.join(temp_scrapy_dir, tmp_file_name)

        if self._run_scrapy_spider(spider_name, start_url_for_spider, target_domain, tmp_output_file_path, max_items_per_scrape, search_query_for_spider):
            try:
                with open(tmp_output_file_path, 'r', encoding='utf-8') as f: raw_data = json.load(f)
                if isinstance(raw_data, list):
                    for item_dict in raw_data: # item_dict is from PapriVideoItem
                        # Convert to the common format for the orchestrator
                        # This mapping should align with PapriVideoItem fields
                        # Using .get for safety for all fields
                        conv = {
                            'original_url': item_dict.get('original_url'),
                            'platform_name': item_dict.get('platform_name', f'Scraped_{target_domain}'),
                            'platform_video_id': item_dict.get('platform_video_id'),
                            'title': item_dict.get('title'),
                            'description': " ".join(item_dict.get('description', [])) if isinstance(item_dict.get('description'), list) else item_dict.get('description'),
                            'thumbnail_url': item_dict.get('thumbnail_url'),
                            'publication_date': self._parse_datetime_str_to_iso(item_dict.get('publication_date_str')),
                            'duration_seconds': self._parse_duration_str_to_seconds(item_dict.get('duration_str')),
                            'uploader_name': item_dict.get('uploader_name'),
                            'uploader_url': item_dict.get('uploader_url'),
                            'tags': item_dict.get('tags', []),
                            'view_count': int(str(item_dict.get('view_count_str','0')).replace(',','').split(' ')[0]) if item_dict.get('view_count_str','0').replace(',','').split(' ')[0].isdigit() else 0,
                            'like_count': int(str(item_dict.get('like_count_str','0')).replace(',','').split(' ')[0]) if item_dict.get('like_count_str','0').replace(',','').split(' ')[0].isdigit() else 0,
                            'dislike_count': int(str(item_dict.get('dislike_count_str','0')).replace(',','').split(' ')[0]) if item_dict.get('dislike_count_str','0').replace(',','').split(' ')[0].isdigit() else 0,
                            'language_code_video': item_dict.get('language_code_video'), # Language of video
                            'licence_str': item_dict.get('licence_str'),
                            'category_str': item_dict.get('category_str'),
                            'privacy_str': item_dict.get('privacy_str'),
                            'instance_url': item_dict.get('instance_url'),
                            'transcript_vtt_url': item_dict.get('transcript_vtt_url'), # Crucial
                            'language_code_caption': item_dict.get('language_code_caption'), # Crucial
                            'embed_url': item_dict.get('embed_url'),
                            'direct_video_url': item_dict.get('direct_video_url'),
                            'raw_scraped_ld_json': item_dict.get('ld_json_data') # Pass for potential further processing
                        }
                        if conv['original_url'] and conv['title'] and conv['platform_video_id']: # Essential fields
                            converted_items.append(conv)
                        # else: logger.warning(f"SOIAgent: Scraped item missing essential fields: {item_dict.get('title')}, URL: {item_dict.get('original_url')}")
                else: logger.warning(f"SOIAgent: Scrapy output {tmp_output_file_path} not a list.")
            except json.JSONDecodeError: logger.error(f"SOIAgent: Failed to decode JSON: {tmp_output_file_path}", exc_info=True)
            except Exception as e: logger.error(f"SOIAgent: Error processing Scrapy output for {platform_config['name']}: {e}", exc_info=True)
        # Ensure cleanup
        if os.path.exists(tmp_output_file_path):
            try: os.remove(tmp_output_file_path)
            except Exception as e_del: logger.error(f"SOIAgent: Failed to delete temp output {tmp_output_file_path}: {e_del}")

        logger.info(f"SOIAgent: {platform_config['name']} scraping -> {len(converted_items)} items.")
        return converted_items

    def fetch_content_from_sources(self, processed_query_data): # 
        # ... (API calls to YouTube, Vimeo, Dailymotion as before using `max_api_results`) ...
        all_source_results = []; query_text_for_apis = processed_query_data.get('processed_query', ''); query_original_text = processed_query_data.get('original_query', '')
        max_api_results = getattr(settings, 'MAX_API_RESULTS_PER_SOURCE', 7)
        max_scraped_items = getattr(settings, 'MAX_SCRAPED_ITEMS_PER_SOURCE', 5)

        if query_text_for_apis: # API calls only if text query part exists
            # ... (self.search_youtube, self.search_vimeo, self.search_dailymotion calls)
            pass # These methods should be defined elsewhere in the class

        # === [YOU] CONFIGURE `scrapeable_platforms` with your actual targets ===
        scrapeable_platforms = [] 
        # Example: This should be populated from Django settings or a DB config for flexibility
        # if getattr(settings, 'ENABLE_PEERTUBE_TILVIDS_SCRAPER', False): # Example flag
        #     scrapeable_platforms.append({
        #         'name': 'PeerTube_Tilvids', 'spider_name': 'peertube', 
        #         'base_url': 'https://tilvids.com', 
        #         'search_path_template': '/search/videos?search={query}&searchTarget=local', 
        #         'default_listing_url': 'https://tilvids.com/videos/recently-added'
        #     })
        # IMPORTANT: Add your actual platform configurations here based on your research and spider development
        
        if scrapeable_platforms and query_original_text and processed_query_data.get('intent') in ['general_video_search', 'hybrid_text_visual_search']:
            for platform_config in scrapeable_platforms:
                time.sleep(getattr(settings, 'SCRAPE_INTER_PLATFORM_DELAY_SECONDS', 2)) # Configurable delay
                scraped_data = self.search_scraped_platform(platform_config, query_original_text, max_items_per_scrape=max_scraped_items)
                all_source_results.extend(scraped_data)
        
        logger.info(f"SOIAgent: Total raw results (API + Scraped): {len(all_source_results)}")
        return all_source_results

    # Define or ensure search_youtube, search_vimeo, search_dailymotion methods are present
    # These would use 'requests' library and API keys from settings.
    # Example structure (implement fully based on earlier steps):
    def search_youtube(self, query, max_results=5): logger.debug(f"Youtube stub for '{query}'"); return []
    def search_vimeo(self, query, max_results=5): logger.debug(f"Vimeo search stub for '{query}'"); return []
    def search_dailymotion(self, query, max_results=5): logger.debug(f"Dailymotion search stub for '{query}'"); return []
