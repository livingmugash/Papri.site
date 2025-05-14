# backend/ai_agents/result_aggregation_agent.py

from collections import Counter

class ResultAggregationAgent:
    def __init__(self):
        print("ResultAggregationAgent initialized.")

    def aggregate_and_rank_results(self, persisted_video_source_objects, processed_query_data, all_analysis_data):
        """
        Aggregates, (eventually deduplicates), and ranks results.
        
        persisted_video_source_objects: List of VideoSource Django model instances.
        processed_query_data: Output from QueryUnderstandingAgent (contains 'keywords').
        all_analysis_data: Dict keyed by video_source_obj.id, containing analysis outputs from CAAgent
                           (e.g., {'transcript_analysis': {'keywords': [...], ...}}).
        
        Returns: A list of VideoSource Django model instances, ranked.
                 Or, for now, a list of Papri Video model IDs, ranked.
        """
        print(f"RARAgent: Aggregating and ranking {len(persisted_video_source_objects)} video sources.")

        if not persisted_video_source_objects:
            return []

        query_keywords = set(k.lower() for k in processed_query_data.get('keywords', []))
        if not query_keywords:
            print("RARAgent: No query keywords provided for ranking. Returning in original order (or by date if available).")
            # Fallback: sort by publication date if no keywords (newest first)
            # This requires that persisted_video_source_objects have their .video.publication_date populated
            try:
                sorted_sources = sorted(
                    persisted_video_source_objects,
                    key=lambda vs: (vs.video.publication_date is not None, vs.video.publication_date), # Sort by whether date exists, then by date
                    reverse=True
                )
                return [vs.video.id for vs in sorted_sources if vs.video]
            except Exception as e:
                print(f"RARAgent: Error during fallback sort: {e}. Returning as is.")
                return [vs.video.id for vs in persisted_video_source_objects if vs.video]


        ranked_sources_with_scores = []

        for vs_obj in persisted_video_source_objects:
            score = 0
            video_keywords = set()

            # Get keywords from transcript analysis if available
            analysis_data_for_source = all_analysis_data.get(vs_obj.id, {})
            transcript_analysis = analysis_data_for_source.get('transcript_analysis', {})
            if transcript_analysis and transcript_analysis.get('status') == 'processed':
                video_keywords.update(k.lower() for k in transcript_analysis.get('keywords', []))

            # Get keywords from title (simple split and lowercasing for now)
            if vs_obj.video and vs_obj.video.title:
                title_words = set(word.lower() for word in vs_obj.video.title.split())
                video_keywords.update(title_words)
            
            # Get keywords from description (simple split for now)
            if vs_obj.video and vs_obj.video.description:
                desc_words = set(word.lower() for word in vs_obj.video.description.split()[:50]) # Limit to first 50 words
                video_keywords.update(desc_words)

            # Calculate score based on keyword overlap
            matching_keywords = query_keywords.intersection(video_keywords)
            score = len(matching_keywords)

            # Bonus for exact phrase match in title (very basic)
            if vs_obj.video and vs_obj.video.title and processed_query_data.get('processed_query'):
                if processed_query_data['processed_query'].lower() in vs_obj.video.title.lower():
                    score += 5 # Arbitrary bonus

            ranked_sources_with_scores.append({'video_source': vs_obj, 'score': score})

        # Sort by score (descending), then perhaps by publication date as a tie-breaker
        ranked_sources_with_scores.sort(
            key=lambda x: (
                x['score'], 
                x['video_source'].video.publication_date if x['video_source'].video and x['video_source'].video.publication_date else timezone.datetime.min.replace(tzinfo=timezone.utc)
            ), 
            reverse=True
        )
        
        # Extract ranked VideoSource objects or their Video IDs
        # We need to ensure we don't have duplicate Papri Video IDs if multiple sources point to the same video.
        # The current flow in orchestrator._persist_basic_video_info tries to link to one canonical Video.
        
        ranked_papri_video_ids = []
        seen_papri_video_ids = set()
        for item in ranked_sources_with_scores:
            vs_obj = item['video_source']
            if vs_obj.video: # Ensure the VideoSource is linked to a canonical Video
                if vs_obj.video.id not in seen_papri_video_ids:
                    ranked_papri_video_ids.append(vs_obj.video.id)
                    seen_papri_video_ids.add(vs_obj.video.id)
        
        print(f"RARAgent: Ranking complete. Returning {len(ranked_papri_video_ids)} unique Papri Video IDs.")
        return ranked_papri_video_ids

    def perform_deduplication(self, video_source_objects):
        """
        Placeholder for more advanced deduplication.
        Currently, deduplication is handled at the VideoSource level by original_url
        and the linking to canonical Video objects in the orchestrator.
        This method could implement content-based deduplication later.
        """
        print(f"RARAgent: Deduplication (placeholder) called for {len(video_source_objects)} sources.")
        # For now, assume orchestrator's _persist_basic_video_info handles basic Video linking.
        # Return unique Video objects based on the linking in persisted_video_source_objects.
        unique_videos = {} # papri_video_id -> video_source_object (first one encountered)
        for vs_obj in video_source_objects:
            if vs_obj.video and vs_obj.video.id not in unique_videos:
                unique_videos[vs_obj.video.id] = vs_obj
        
        return list(unique_videos.values())
