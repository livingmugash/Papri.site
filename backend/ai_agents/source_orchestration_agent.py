
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
