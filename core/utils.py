import re

def generate_referral_code(user_id):
    """Generates a referral code based on user ID."""
    return f"r{user_id}"

def get_referrer_id_from_code(code):
    """Extracts user ID from referral code."""
    if code.startswith("r") and code[1:].isdigit():
        return int(code[1:])
    return None

def strip_html(text):
    """Removes HTML tags from text."""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def safe_split_text(text, limit=4000):
    """
    Splits text into chunks of maximum 'limit' characters, 
    respecting newlines to avoid breaking HTML tags or sentences.
    """
    if len(text) <= limit:
        return [text]
        
    chunks = []
    current_chunk = ""
    
    # Split by double newline first (paragraphs)
    paragraphs = text.split('\n\n')
    
    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= limit:
            current_chunk += para + "\n\n"
        else:
            # If current chunk is not empty, save it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If paragraph itself is too long, split by single newline
            if len(para) > limit:
                lines = para.split('\n')
                for line in lines:
                    if len(current_chunk) + len(line) + 1 <= limit:
                        current_chunk += line + "\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                        # If line is still too long, hard split (rare)
                        while len(line) > limit:
                            chunks.append(line[:limit])
                            line = line[limit:]
                        current_chunk = line + "\n"
            else:
                current_chunk = para + "\n\n"
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks
