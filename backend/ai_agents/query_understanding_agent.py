# backend/ai_agents/query_understanding_agent.py
import spacy

class QueryUnderstandingAgent:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm") # Small English model
            # For more languages, you'd load appropriate models
        except OSError:
            print("Downloading spaCy en_core_web_sm model...")
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")


    def process_text_query(self, text_query):
        if not text_query:
            return {'keywords': [], 'entities': [], 'intent': 'general_video_search', 'processed_query': ''}

        doc = self.nlp(text_query)
        keywords = [token.lemma_.lower() for token in doc if not token.is_stop and not token.is_punct and token.pos_ in ['NOUN', 'PROPN', 'VERB', 'ADJ']]
        entities = [{'text': ent.text, 'label': ent.label_} for ent in doc.ents]

        # Basic intent - can be expanded with LLMs or rule-based logic
        intent = "visual_search_with_text" if "image of" in text_query.lower() or "show me a picture of" in text_query.lower() else "general_video_search"

        processed_query = " ".join(keywords) # Simplified processed query
        print(f"QAgent - Text: '{text_query}', Keywords: {keywords}, Entities: {entities}, Processed: '{processed_query}'")
        return {'keywords': keywords, 'entities': entities, 'intent': intent, 'processed_query': processed_query}

    def process_image_query(self, image_path_or_data):
        # For now, just acknowledge image receipt. Actual processing in VisualAnalyzer.
        print(f"QAgent - Image received: {image_path_or_data}")
        return {'intent': 'visual_similarity_search', 'image_reference': image_path_or_data}
