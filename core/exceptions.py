class RAGException(Exception):
    """Exception de base pour l'application"""
    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail

class OllamaTimeoutError(RAGException):
    """Levée quand Ollama ne répond pas assez vite"""
    pass

class OllamaError(RAGException):
    """levée quand Ollama retroune une erreur"""
    pass

class DocumentParsingError(RAGException):
    """Levée quand Docling échoue sur un PDF"""
    pass