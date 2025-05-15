
# backend/ai_agents/source_orchestration_agent.py
import requests
import time
from django.conf import settings # To access API keys

class SourceOrchestrationAgent:
    # ... (__init__, API search methods as before) ...
    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.vimeo_access_token = settings.VIMEO_ACCESS_TOKEN
        # Scrapy executable path, found once
        self.scrapy_executable = shutil.which('scrapy')
        if not self.scrapy_executable:
            logger.error("SOIAgent: Scrapy executable not found in PATH. Scraping will be disabled.")
        # Path to the Scrapy project (if you structure it as a full project)
        # For standalone spiders, it's where the spiders directory is.
        self.scrapers_base_dir = os.path.join(settings.BASE_DIR, 'ai_agents', 'scrapers')
        # If you create a scrapy.cfg at self.scrapers_base_dir, Scrapy will treat it as project root.
        # Example minimal scrapy.cfg:
        # [settings]
        # default = scrapers.settings # Assumes scrapers/settings.py
        # [deploy]
        # project = scrapers


    def _run_scrapy_spider(self, spider_name, start_url_for_spider, target_domain_for_spider, output_file_path, max_items_scraped):
        if not self.scrapy_executable:
            logger.error("SOIAgent: Scrapy executable not available. Cannot run spider.")
            return False
        
        command = [
            self.scrapy_executable, 'crawl', spider_name,
            '-a', f'start_url={start_url_for_spider}',
            '-a', f'target_domain={target_domain_for_spider}',
            '-a', f'max_items_to_scrape={max_items_scraped}', # Pass max_items to spider
            '-o', output_file_path,
            '-s', 'LOG_LEVEL=INFO', # Scrapy's own logging
            # To ensure items.py is found if running from a different CWD,
            # you might need to set PYTHONPATH or ensure Scrapy is run from a "project" root.
            # This command assumes spiders are in a 'spiders' subdir of `self.scrapers_base_dir`
            # and items.py is also in `self.scrapers_base_dir` or configured in a Scrapy settings file.
        ]
        
        logger.info(f"SOIAgent: Running Scrapy: {' '.join(command)}")
        try:
            # Running from scrapers_base_dir assumes your spiders and items are structured relative to it.
            process = subprocess.run(command, cwd=self.scrapers_base_dir, capture_output=True, text=True, check=False, timeout=300, encoding='utf-8', errors='ignore')
            
            if process.returncode != 0:
                logger.error(f"SOIAgent: Scrapy spider '{spider_name}' failed for {start_url_for_spider}. Code: {process.returncode}. Stderr: {process.stderr[-500:]}")
                return False
            
            logger.info(f"SOIAgent: Scrapy spider '{spider_name}' completed for {start_url_for_spider}. Output: {output_file_path}")
            return True
        except subprocess.TimeoutExpired: # ...
            logger.error(f"SOIAgent: Scrapy spider '{spider_name}' timed out for {start_url_for_spider}.")
            return False
        except Exception as e: # ...
            logger.error(f"SOIAgent: Exception running Scrapy spider '{spider_name}' for {start_url_for_spider}: {e}")
            return False

    def _parse_duration_str(self, duration_str): # Renamed from _parse_duration
        # ... (Robust duration parsing logic as sketched before) ...
        # Example for PTxMxS and HH:MM:SS or MM:SS
        if not duration_str: return None
        import re
        duration_str = str(duration_str).upper()
        if duration_str.startswith("PT"): # ISO 8601 Duration like PT10M32S or PT1H5M2S
            h, m, s = 0, 0, 0
            h_match = re.search(r'(\d+)H', duration_str)
            if h_match: h = int(h_match.group(1))
            m_match = re.search(r'(\d+)M', duration_str)
            if m_match: m = int(m_match.group(1))
            s_match = re.search(r'(\d+)S', duration_str)
            if s_match: s = int(s_match.group(1))
            return h * 3600 + m * 60 + s
        else: # Try HH:MM:SS or MM:SS or SS
            parts = [int(p) for p in duration_str.split(':') if p.isdigit()]
            if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
            if len(parts) == 2: return parts[0]*60 + parts[1]
            if len(parts) == 1: return parts[0]
        return None
        
    def _parse_publication_date(self, date_str):
        if not date_str: return None
        from dateutil import parser
        try:
            # robustly parse various date formats
            dt_obj = parser.parse(date_str)
            # Convert to UTC if timezone naive, or ensure it's aware and UTC
            if dt_obj.tzinfo is None:
                dt_obj = timezone.make_aware(dt_obj, timezone.get_default_timezone()) # Assume default Django TZ
            return dt_obj.astimezone(timezone.utc).isoformat() # Standard ISO format string
        except (ValueError, TypeError):
            logger.warning(f"SOIAgent: Could not parse date string: {date_str}")
            return None


    def search_scraped_platform(self, platform_config, query_text, max_items=10):
        """
        Generic method to search a platform using its configured Scrapy spider.
        platform_config: dict like {'name': 'PeerTube_tilvids.com', 'spider_name': 'peertube', 
                                     'base_url': 'https://tilvids.com', 
                                     'search_path_template': '/search/videos?search={query}'}
        """
        spider_name = platform_config['spider_name']
        base_url = platform_config['base_url']
        target_domain = urlparse(base_url).netloc

        # Construct start URL: if platform has a search path, use it. Otherwise, spider might browse.
        if platform_config.get('search_path_template') and query_text:
            search_path = platform_config['search_path_template'].format(query=requests.utils.quote(query_text))
            start_url_for_spider = base_url.rstrip('/') + search_path
        else: # Fallback to a generic listing page defined in platform_config or spider default
            start_url_for_spider = platform_config.get('default_listing_url', base_url)
        
        logger.info(f"SOIAgent: Scraping {platform_config['name']} via spider '{spider_name}', start URL: {start_url_for_spider}")
        
        scraped_items_converted = []
        # Create a temporary file for Scrapy output within MEDIA_ROOT/temp_scrapy_outputs
        temp_scrapy_dir = os.path.join(settings.MEDIA_ROOT, "temp_scrapy_outputs")
        os.makedirs(temp_scrapy_dir, exist_ok=True)

        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json', dir=temp_scrapy_dir, prefix=f"{spider_name}_") as tmp_output_file:
            tmp_output_file_path = tmp_output_file.name
        
        if self._run_scrapy_spider(spider_name, start_url_for_spider, target_domain, tmp_output_file_path, max_items):
            try:
                with open(tmp_output_file_path, 'r', encoding='utf-8') as f:
                    raw_scraped_data = json.load(f) # Assumes Scrapy outputs a JSON list
                
                if isinstance(raw_scraped_data, list):
                    for item in raw_scraped_data:
                        # Basic filtering if spider didn't handle search query directly (less efficient)
                        title_desc = (item.get('title','_') + item.get('description','_')).lower()
                        if query_text and not all(kw.lower() in title_desc for kw in query_text.split() if len(kw)>2):
                             # If query_text provided and not all its significant words are in title/desc, skip
                             # This is a very loose filter. Spider-level search is better.
                             # logger.info(f"SOIAgent: Skipping item '{item.get('title')}' due to post-scrape keyword filter mismatch for query '{query_text}'.")
                             pass # For now, let's not filter here and let RARAgent do it, or improve spider.

                        converted = {
                            'platform_name': item.get('platform_name', platform_config['name']),
                            'platform_video_id': item.get('platform_video_id'),
                            'title': item.get('title'),
                            'description': item.get('description'),
                            'thumbnail_url': item.get('thumbnail_url'),
                            'publication_date': self._parse_publication_date(item.get('publication_date_str')),
                            'duration_seconds': self._parse_duration_str(item.get('duration_str')),
                            'original_url': item.get('original_url'),
                            'embed_url': item.get('embed_url') or item.get('direct_video_url'),
                            'uploader_name': item.get('uploader_name'),
                            'tags': item.get('tags', []),
                            # TODO: Transcript handling (download VTT if transcript_vtt_url exists)
                        }
                        # Ensure essential fields are present
                        if converted['original_url'] and converted['title']:
                            scraped_items_converted.append(converted)
                else:
                    logger.warning(f"SOIAgent: Scrapy output for {platform_config['name']} was not a list.")
            except json.JSONDecodeError:
                logger.error(f"SOIAgent: Failed to decode JSON from Scrapy output: {tmp_output_file_path}")
            except Exception as e:
                logger.error(f"SOIAgent: Error processing Scrapy output for {platform_config['name']}: {e}")
            finally:
                if os.path.exists(tmp_output_file_path): os.remove(tmp_output_file_path)
        else: # Spider run failed
             if os.path.exists(tmp_output_file_path): os.remove(tmp_output_file_path) # Still cleanup

        logger.info(f"SOIAgent: {platform_config['name']} scraping yielded {len(scraped_items_converted)} converted items.")
        return scraped_items_converted


    def fetch_content_from_sources(self, processed_query_data):
        all_source_results = []
        query_text_for_apis = processed_query_data.get('processed_query', '') # Use QAgent's processed query for APIs
        query_original_text = processed_query_data.get('original_query', '') # Use original for scrapers if better

        # --- API Sources ---
        if query_text_for_apis: # Only call APIs if there's text
            # ... (search_youtube, search_vimeo, search_dailymotion calls as before using query_text_for_apis) ...
            all_source_results.extend(self.search_youtube(query_text_for_apis, max_results=7))
            all_source_results.extend(self.search_vimeo(query_text_for_apis, max_results=7))
            all_source_results.extend(self.search_dailymotion(query_text_for_apis, max_results=7))


        # --- Scraped Sources (Example) ---
        # This would come from a configuration or database of scrapeable platforms
        scrapeable_platforms = [
            {
                'name': 'PeerTube_Tilvids', 'spider_name': 'peertube', 
                'base_url': 'https://tilvids.com', 
                # Tilvids search: https://tilvids.com/search/videos?search=QUERY&searchTarget=local # searchTarget=local or instances
                'search_path_template': '/search/videos?search={query}&searchTarget=local', 
                'default_listing_url': 'https://tilvids.com/videos/recently-added' # Fallback if no query
            },
            # Add other PeerTube instances or different platforms (Odysee, Rumble etc. would need own spiders)
            # {
            #     'name': 'Odysee', 'spider_name': 'odysee_spider', # Hypothetical
            #     'base_url': 'https://odysee.com',
            #     'search_path_template': '/$/search?q={query}'
            # }
        ]

        # Only scrape if it's primarily a text query, or if hybrid query specifies text.
        # Avoid broad scraping for pure visual queries unless a specific strategy is in place.
        if query_original_text and processed_query_data.get('intent') in ['general_video_search', 'hybrid_text_visual_search']:
            for platform_config in scrapeable_platforms:
                time.sleep(0.5) # Basic courtesy delay between different platforms/spiders
                scraped_data = self.search_scraped_platform(platform_config, query_original_text, max_items=5) # Limit items per scraped source
                all_source_results.extend(scraped_data)
        
        logger.info(f"SOIAgent: Total raw results from ALL sources (API + Scraped): {len(all_source_results)}")
        return all_source_results

