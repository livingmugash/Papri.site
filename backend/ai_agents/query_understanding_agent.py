# backend/ai_agents/query_understanding_agent.py
import spacy
from django.conf import settings
import os
import re
from sentence_transformers import SentenceTransformer # Add this

AGENT_NAME = "QueryUnderstandingAgent"

class QueryUnderstandingAgent:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # ... (spacy model download logic) ...
            self.nlp = spacy.load("en_core_web_sm")
        
        try:
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            print("QueryUnderstandingAgent: SentenceTransformer model loaded.")
        except Exception as e:
            print(f"QueryUnderstandingAgent: CRITICAL - Failed to load SentenceTransformer model: {e}")
            self.embedding_model = None

    def _generate_query_embedding(self, text_query):
        if not self.embedding_model or not text_query:
            return None
        try:
            embedding = self.embedding_model.encode(text_query, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"QueryUnderstandingAgent: Error generating query embedding: {e}")
            return None

    def process_query(self, search_params):
        """
        Processes the raw search parameters (text or image reference)
        and extracts keywords, entities, intent, etc.
        """
        query_text = search_params.get('query_text')
        image_ref = search_params.get('query_image_ref')
        processed_data = {'original_params': search_params}

        if query_text and self.nlp:
            doc = self.nlp(query_text)
            keywords = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']]
            entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]
            processed_query_text = " ".join(keywords)
            
            processed_data.update({
                'type': 'text_search',
                'keywords': keywords,
                'entities': entities,
                'processed_query_text': processed_query_text,
                'intent': 'general_video_search' # Basic intent, can be refined
            })
            print(f"QAgent (Task {self.papri_task_id}): Processed text query. Keywords: {keywords}")
        elif image_ref:
            processed_data.update({
                'type': 'image_search',
                'image_reference': image_ref,
                'intent': 'visual_similarity_search'
            })
            if query_text: # Hybrid search
                 processed_data['accompanying_text'] = query_text # Store for context
                 doc = self.nlp(query_text) # Process accompanying text as well
                 keywords = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']]
                 processed_data['accompanying_keywords'] = keywords
                 print(f"QAgent (Task {self.papri_task_id}): Processed image query with accompanying text. Keywords: {keywords}")
            else:
                print(f"QAgent (Task {self.papri_task_id}): Processed image query. Ref: {image_ref}")
        else:
            print(f"QAgent (Task {self.papri_task_id}): No valid query input found.")
            processed_data.update({'type': 'empty_search', 'intent': 'none'})
            # raise ValueError("No query text or image reference provided to QAgent.") # Or handle gracefully

        return processed_data


def process_image_query(self, image_path_or_data):
        # ... (existing logic) ...
        print(f"QAgent - Image received: {image_path_or_data}")
        return {'intent': 'visual_similarity_search', 'image_reference': image_path_or_data, 'query_embedding': None}
