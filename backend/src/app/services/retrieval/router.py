import re

class QueryRouter:
    """
    Industry-standard Intent Classifier.
    Routes queries to Greeting, Thanks, or the RAG Pipeline.
    """
    def __init__(self):
        # Regex patterns for common greetings and small talk
        self.greeting_patterns = [
            r"^(hi|hello|hey|hola|greetings|good morning|good afternoon|good evening)(\s+there)?[\s!.]*$"
        ]
        self.thanks_patterns = [
            r"^(thanks|thank you|thx|appreciate it)[\s!.]*$"
        ]

    def get_intent(self, query: str) -> str:
        query_lower = query.lower().strip()
        
        for pattern in self.greeting_patterns:
            if re.match(pattern, query_lower):
                return "GREETING"
                
        for pattern in self.thanks_patterns:
            if re.match(pattern, query_lower):
                return "THANKS"
                
        return "RAG_QUERY"