import httpx
from typing import Optional, Dict, Any
from app.core.config import Settings, get_settings


class OpenRouterService:
    """
    Service for interacting with OpenRouter API.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.timeout = settings.OPENROUTER_TIMEOUT
    
    async def chat_completion(
        self,
        messages: list[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            API response dictionary
        """
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",  # Optional
            "X-Title": self.settings.APP_NAME  # Optional
        }
        
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def test_connection(self) -> bool:
        """
        Test the OpenRouter API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            result = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return bool(result)
        except Exception:
            return False


def get_openrouter_service() -> OpenRouterService:
    """
    Dependency injection for OpenRouter service.
    """
    settings = get_settings()
    return OpenRouterService(settings)
