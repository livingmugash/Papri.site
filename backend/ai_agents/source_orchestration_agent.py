
# backend/ai_agents/source_orchestration_agent.py
import requests
import time
from django.conf import settings # To access API keys

class SourceOrchestrationAgent:
    def __init__(self):
        self.youtube_api_key = settings.YOUTUBE_API_KEY
        self.vimeo_access_token = settings.VIMEO_ACCESS_TOKEN
        # Dailymotion - their API is a bit different, often public access for search

    def search_youtube(self, query_text, max_results=5):
        print(f"SOIAgent - Searching YouTube for: {query_text}")
        if not self.youtube_api_key:
            print("SOIAgent - YouTube API Key not configured.")
            return []

        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query_text,
            'key': self.youtube_api_key,
            'maxResults': max_results,
            'type': 'video'
        }
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            videos = []
            for item in results.get('items', []):
                video_id = item.get('id', {}).get('videoId')
                if video_id:
                    videos.append({
                        'platform_name': 'YouTube',
                        'platform_video_id': video_id,
                        'title': item.get('snippet', {}).get('title'),
                        'description': item.get('snippet', {}).get('description'),
                        'thumbnail_url': item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url'),
                        'publication_date': item.get('snippet', {}).get('publishedAt'),
                        'original_url': f"https://www.youtube.com/watch?v={video_id}"
                        # TODO: Get duration, more details using videos endpoint if needed
                    })
            print(f"SOIAgent - YouTube found {len(videos)} videos.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"SOIAgent - Error searching YouTube: {e}")
            return []
        except Exception as e:
            print(f"SOIAgent - Unexpected error in Youtube: {e}")
            return []


    def search_vimeo(self, query_text, max_results=5):
        print(f"SOIAgent - Searching Vimeo for: {query_text}")
        if not self.vimeo_access_token:
            print("SOIAgent - Vimeo Access Token not configured.")
            return []

        search_url = "https://api.vimeo.com/videos"
        headers = {
            'Authorization': f'Bearer {self.vimeo_access_token}',
            'Accept': 'application/vnd.vimeo.*+json;version=3.4'
        }
        params = {
            'query': query_text,
            'per_page': max_results,
            'sort': 'relevant', # or 'date', 'alphabetical', 'plays', 'likes', 'comments', 'duration'
            'direction': 'desc'
        }
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            videos = []
            for item in results.get('data', []):
                videos.append({
                    'platform_name': 'Vimeo',
                    'platform_video_id': item.get('uri', '').split('/')[-1] if item.get('uri') else None,
                    'title': item.get('name'),
                    'description': item.get('description'),
                    'thumbnail_url': item.get('pictures', {}).get('base_link') if item.get('pictures') else None,
                    'publication_date': item.get('created_time'),
                    'duration_seconds': item.get('duration'),
                    'original_url': item.get('link'),
                    'embed_url': item.get('player_embed_url')
                })
            print(f"SOIAgent - Vimeo found {len(videos)} videos.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"SOIAgent - Error searching Vimeo: {e}")
            return []
        except Exception as e:
            print(f"SOIAgent - Unexpected error in Vimeo search: {e}")
            return []

    def search_dailymotion(self, query_text, max_results=5):
        print(f"SOIAgent - Searching Dailymotion for: {query_text}")
        # Dailymotion public API for search (no key needed for basic search)
        # https://developers.dailymotion.com/api/#video-search
        search_url = "https://api.dailymotion.com/videos"
        params = {
            'fields': 'id,title,description,thumbnail_large_url,created_time,duration,url,embed_url',
            'search': query_text,
            'limit': max_results,
            'sort': 'relevance' # or 'recent', 'visited', 'visited-hour', 'visited-today', 'visited-week', 'visited-month'
        }
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json()
            videos = []
            for item in results.get('list', []):
                videos.append({
                    'platform_name': 'Dailymotion',
                    'platform_video_id': item.get('id'),
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'thumbnail_url': item.get('thumbnail_large_url'),
                    'publication_date': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(item.get('created_time'))) if item.get('created_time') else None, # Convert timestamp
                    'duration_seconds': item.get('duration'),
                    'original_url': item.get('url'),
                    'embed_url': item.get('embed_url')
                })
            print(f"SOIAgent - Dailymotion found {len(videos)} videos.")
            return videos
        except requests.exceptions.RequestException as e:
            print(f"SOIAgent - Error searching Dailymotion: {e}")
            return []
        except Exception as e:
            print(f"SOIAgent - Unexpected error in Dailymotion search: {e}")
            return []


    def fetch_content_from_sources(self, processed_query_data):
        # This is a simplified orchestrator for fetching
        all_source_results = []
        query_text = processed_query_data.get('processed_query', '') # Use processed query

        if not query_text and processed_query_data.get('intent') != 'visual_similarity_search':
            print("SOIAgent - No query text to search with.")
            return all_source_results

        # For text search intent
        if processed_query_data.get('intent') == 'general_video_search' and query_text:
            youtube_results = self.search_youtube(query_text)
            all_source_results.extend(youtube_results)
            time.sleep(0.5) # Basic rate limiting

            vimeo_results = self.search_vimeo(query_text)
            all_source_results.extend(vimeo_results)
            time.sleep(0.5)

            dailymotion_results = self.search_dailymotion(query_text)
            all_source_results.extend(dailymotion_results)

        # For image search intent, SOIAgent's role might be different (e.g., finding videos
        # that then need frame analysis by CAAgent, or directly querying image-searchable video APIs if they exist)
        # For now, we assume image search primarily relies on our indexed visual features.
        # If a text query accompanies an image search, it might be used to filter candidate videos.

        print(f"SOIAgent - Total raw results from APIs: {len(all_source_results)}")
        return all_source_results


def _run_scrapy_spider(self, spider_name, start_url, output_file_path):
        """
        Runs a Scrapy spider as a subprocess.
        spider_name: Name of the spider (e.g., 'peertube').
        start_url: The initial URL for the spider to crawl.
        output_file_path: Path to save the JSON output.
        Returns True if successful, False otherwise.
        """
        scrapy_project_dir = os.path.join(settings.BASE_DIR, 'ai_agents', 'scrapers') # Path to where spiders are
        scrapy_executable = shutil.which('scrapy') # Find scrapy executable

        if not scrapy_executable:
            self.logger.error("Scrapy executable not found in PATH.")
            return False
        
        # Ensure allowed_domains is correctly set if spider uses it.
        # The spider init can take start_url and derive allowed_domains.
        command = [
            scrapy_executable,
            'crawl',
            spider_name,
            '-a', f'start_url={start_url}',
            '-o', output_file_path, # Output items to a JSON file
            '-s', 'LOG_LEVEL=INFO', # Control Scrapy log level
            # '--nolog' # To suppress Scrapy logs almost entirely if too noisy
        ]
        
        self.logger.info(f"SOIAgent: Running Scrapy command: {' '.join(command)} from cwd: {scrapy_project_dir}")
        try:
            # Run from the directory containing scrapy.cfg if you have one, or where spiders are.
            # For now, assuming spiders can be run from anywhere if settings are self-contained or passed via -s.
            # If your spiders are part of a Scrapy project, you must run 'scrapy crawl' from the project's root.
            # This current setup assumes spiders are standalone runnable.
            process = subprocess.run(command, cwd=scrapy_project_dir, capture_output=True, text=True, check=False, timeout=300) # 5 min timeout
            
            if process.returncode != 0:
                self.logger.error(f"SOIAgent: Scrapy spider '{spider_name}' failed for {start_url}. Return code: {process.returncode}")
                self.logger.error(f"Stderr: {process.stderr[-500:]}") # Log last 500 chars of error
                return False
            
            self.logger.info(f"SOIAgent: Scrapy spider '{spider_name}' completed for {start_url}. Output at {output_file_path}")
            return True
        except subprocess.TimeoutExpired:
            self.logger.error(f"SOIAgent: Scrapy spider '{spider_name}' timed out for {start_url}.")
            return False
        except Exception as e:
            self.logger.error(f"SOIAgent: Exception running Scrapy spider '{spider_name}' for {start_url}: {e}")
            return False

    def search_peertube_instance(self, instance_base_url, query_text, max_items_overall=10):
        """
        Searches a PeerTube instance using a conceptual Scrapy spider.
        NOTE: PeerTube instances often have their own search API (?search=query) which might be better than broad crawling.
              This method demonstrates general scraping.
        """
        self.logger.info(f"SOIAgent: Scraping PeerTube instance {instance_base_url} for query '{query_text}' (conceptual).")
        
        # For PeerTube, direct search URL is usually like: {instance_base_url}/search/videos?search={query_text}
        # The spider would start there.
        # However, the generic spider above starts from a listing page.
        # This part needs to align with how your spider is designed to receive search queries or start pages.

        # For a generic spider that browses, the query_text might not be directly used by the spider's start_url.
        # The spider would fetch many videos, and filtering by query_text would happen post-scraping.
        # This is INEFFICIENT for targeted search.
        # A BETTER spider would take the query and use PeerTube's search URL.

        # For now, let's assume the spider starts from a general video listing (e.g., /videos/local)
        # and we'll filter results later. This is just to get the scraping mechanism working.
        
        scraped_items = []
        # Create a temporary file for Scrapy output
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.json', dir=settings.MEDIA_ROOT) as tmp_output_file:
            tmp_output_file_path = tmp_output_file.name
        
        # Example start URL (replace with actual logic, e.g., using PeerTube's search endpoint)
        # For actual search: target_start_url = f"{instance_base_url}/search/videos?search={requests.utils.quote(query_text)}"
        target_start_url = f"{instance_base_url}/videos/recently-added" # Example generic page

        if self._run_scrapy_spider('peertube', target_start_url, tmp_output_file_path):
            try:
                with open(tmp_output_file_path, 'r') as f:
                    # Scrapy -o outputs one JSON object per line if format is jsonlines (default for .jsonl)
                    # or a single JSON array if format is json. Assume JSON array for now.
                    try:
                        raw_scraped_data = json.load(f)
                        if isinstance(raw_scraped_data, list):
                            for item in raw_scraped_data:
                                # Convert to the common format expected by the orchestrator
                                # This mapping depends on your PapriVideoItem fields
                                converted_item = {
                                    'platform_name': item.get('platform_name', 'PeerTubeScraped'),
                                    'platform_video_id': item.get('platform_video_id'),
                                    'title': item.get('title'),
                                    'description': item.get('description'),
                                    'thumbnail_url': item.get('thumbnail_url'),
                                    'publication_date': item.get('publication_date_str'), # Needs parsing
                                    'duration_seconds': self._parse_duration(item.get('duration_str')), # Needs parsing
                                    'original_url': item.get('original_url'),
                                    'embed_url': item.get('embed_url') or item.get('direct_video_url')
                                    # Add other fields as needed
                                }
                                # Filter by query_text (rudimentary) if spider didn't use search endpoint
                                if query_text and query_text.lower() not in (converted_item.get('title','').lower() + converted_item.get('description','').lower()):
                                    continue # Skip if no keyword match (very basic filtering)
                                scraped_items.append(converted_item)
                                if len(scraped_items) >= max_items_overall: break
                        else:
                             self.logger.warning(f"SOIAgent: Scrapy output for PeerTube was not a list: {type(raw_scraped_data)}")
                    except json.JSONDecodeError:
                        self.logger.error(f"SOIAgent: Failed to decode JSON from Scrapy output: {tmp_output_file_path}")
            finally:
                os.remove(tmp_output_file_path) # Clean up temp file
        
        self.logger.info(f"SOIAgent: PeerTube scraping yielded {len(scraped_items)} items after basic filtering.")
        return scraped_items

    def _parse_duration(self, duration_str): # Helper
        if not duration_str: return None
        # Example: "PT10M32S" (ISO 8601 duration) or "10:32"
        # This needs robust parsing based on what PeerTube (or other sites) provide.
        # For now, a very simple H:M:S or M:S parser
        parts = str(duration_str).split(':')
        try:
            if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
            if len(parts) == 2: return int(parts[0])*60 + int(parts[1])
            if len(parts) == 1 and duration_str.upper().startswith("PT"): # Basic ISO 8601 like PT10M32S
                # Rudimentary ISO 8601 duration parsing (only M and S)
                import re
                m = re.search(r'(\d+)M', duration_str.upper())
                s = re.search(r'(\d+)S', duration_str.upper())
                return (int(m.group(1)) * 60 if m else 0) + (int(s.group(1)) if s else 0)
            return int(duration_str) # Assume seconds if single number
        except: return None


    def fetch_content_from_sources(self, processed_query_data):
        all_source_results = []
        query_text = processed_query_data.get('processed_query', '')
        # ... (existing API calls for YouTube, Vimeo, Dailymotion) ...
        # youtube_results = self.search_youtube(query_text)
        # all_source_results.extend(youtube_results); time.sleep(0.2)
        # vimeo_results = self.search_vimeo(query_text)
        # all_source_results.extend(vimeo_results); time.sleep(0.2)
        # dailymotion_results = self.search_dailymotion(query_text)
        # all_source_results.extend(dailymotion_results); time.sleep(0.2)

        # Example: Add scraping for a specific PeerTube instance if query matches certain criteria
        # This logic needs to be much more dynamic based on a list of scrapeable sources.
        if "peertube" in query_text.lower() or True: # For testing, always try scraping one
            # You'd have a list of PeerTube instances to try, or allow users to add them.
            # Replace with an actual, publicly browsable PeerTube instance URL known for SFW content for testing
            test_peertube_instance_url = "https://tilvids.com" # EXAMPLE! CHECK TERMS OF SERVICE
            if test_peertube_instance_url:
                 self.logger.info(f"Attempting to scrape Peertube instance: {test_peertube_instance_url}")
                 peertube_scraped_results = self.search_peertube_instance(test_peertube_instance_url, query_text, max_items_overall=5)
                 all_source_results.extend(peertube_scraped_results)
        
        self.logger.info(f"SOIAgent: Total raw results from ALL sources: {len(all_source_results)}")
        return all_source_results

    # Add a logger to SOIAgent (and other agents) for better debugging
    @property
    def logger(self):
        import logging
        return logging.getLogger(__name__) # Gets a logger named after the module
