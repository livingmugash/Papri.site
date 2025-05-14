# backend/ai_agents/query_understanding_agent.py
import spacy
from django.conf import settings
import os
import re

AGENT_NAME = "QueryUnderstandingAgent"

class QueryUnderstandingAgent:
    def __init__(self, papri_task_id=None):
        self.papri_task_id = papri_task_id
        self.nlp = None
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("QAgent: Downloading spaCy en_core_web_sm model...")
            # Ensure spacy is in your requirements.txt
            # You might need to run this command manually once in your environment:
            # python -m spacy download en_core_web_sm
            # For now, we'll let it error out if not found during init,
            # as automatic download in a worker might be problematic.
            # Consider a management command to download models.
            # For robust error handling:
            # raise RuntimeError("spaCy 'en_core_web_sm' model not found. Please run 'python -m spacy download en_core_web_sm'")
            print("QAgent: spaCy 'en_core_web_sm' model not found. Please ensure it's downloaded.")


        print(f"QAgent initialized for task: {self.papri_task_id if self.papri_task_id else 'Generic'}")

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
