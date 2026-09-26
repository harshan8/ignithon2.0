import json
import ollama

def extract_fraud_timeline_llm(narrative_text: str) -> list:
    """
    Uses a local Ollama LLM to extract chronological timeline events
    from unstructured fraud text in JSON format.
    """
    if not narrative_text or len(narrative_text.strip()) < 10:
        return []

    prompt = f"""
    You are a forensic cybercrime investigator.
    Extract all key events from the following fraud narrative into a chronological timeline.
    
    Return ONLY a valid JSON array of objects. Do not include markdown formatting or extra text.
    Each object must have exactly two keys:
    1. "timestamp_found": The time/date mentioned (or "Unspecified" if implied by sequence).
    2. "event": A concise summary of what happened.

    Narrative:
    \"\"\"{narrative_text}\"\"\"
    """

    try:
        response = ollama.chat(
            model='llama3',
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.1} # Low temperature for accurate JSON formatting
        )
        
        raw_content = response['message']['content'].strip()
        
        # Clean up Markdown wrapper if present (e.g. ```json ... ```)
        if raw_content.startswith("```"):
            raw_content = raw_content.split("```")[1]
            if raw_content.startswith("json"):
                raw_content = raw_content[4:]
        
        extracted_events = json.loads(raw_content.strip())
        return extracted_events if isinstance(extracted_events, list) else []

    except Exception as e:
        # Fallback in case LLM parsing fails
        return [{"timestamp_found": "Error", "event": f"LLM parsing failed: {str(e)}"}]