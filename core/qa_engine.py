import json
import os
import difflib
import re
from typing import Optional, Dict, List

# Singleton to hold loaded data
_QA_DB: List[Dict] = []

def load_qa_db():
    global _QA_DB
    if _QA_DB:
        return _QA_DB
        
    try:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_path, "bot", "data", "ai_qa_db.json")
        
        with open(db_path, "r", encoding="utf-8") as f:
            _QA_DB = json.load(f)
            print(f"Loaded {len(_QA_DB)} Q&A pairs.")
    except Exception as e:
        print(f"Error loading QA DB: {e}")
        _QA_DB = []
        
    return _QA_DB

def normalize_text(text: str) -> str:
    """Lowercase and remove punctuation for better matching"""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return text.strip()

def get_best_match(query: str, threshold: float = 0.65) -> Optional[Dict]:
    """
    Finds the most similar question in the DB.
    Returns the Q&A dict if distinct score > threshold, else None.
    """
    db = load_qa_db()
    if not db:
        return None
        
    norm_query = normalize_text(query)
    best_score = 0
    best_match = None
    
    for item in db:
        # Check similarity with question
        q_norm = normalize_text(item['question'])
        
        # 1. Quick substring check (bonus)
        if norm_query in q_norm or q_norm in norm_query:
             # If significant overlap, boost score but still check ratio
             pass
             
        ratio = difflib.SequenceMatcher(None, norm_query, q_norm).ratio()
        
        # 2. Check similarity with topic (weaker signal but helpful)
        t_ratio = difflib.SequenceMatcher(None, norm_query, normalize_text(item['topic'])).ratio()
        
        final_score = max(ratio, t_ratio * 0.8) # Topic is less weight
        
        if final_score > best_score:
            best_score = final_score
            best_match = item
            
    if best_score >= threshold:
        return {
            "match": best_match,
            "score": best_score
        }
    
    return None
