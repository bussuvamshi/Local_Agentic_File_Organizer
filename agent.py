"""
Semantic Routing Agent for LAFO
Uses LLM to intelligently classify and route documents to appropriate folders.
Supports both Ollama (local) and Gemini (cloud) providers.
"""
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, Any

from config import (
    LLM_PROVIDER,
    OLLAMA_API,
    OLLAMA_MODEL,
    OLLAMA_TIMEOUT,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    ROUTING_SYSTEM_PROMPT,
    CONFIDENCE_THRESHOLD,
    MAX_RETRIES,
    RETRY_DELAY,
    MAX_TEXT_LENGTH
)

logger = logging.getLogger(__name__)

class RoutingAgent:
    """
    Semantic routing agent that uses LLM to classify documents.
    Supports both Ollama (local) and Gemini (cloud) providers.
    Routes documents to appropriate folders based on content analysis.
    """
    
    def __init__(self):
        """Initialize the routing agent."""
        self.provider = LLM_PROVIDER
        self.confidence_threshold = CONFIDENCE_THRESHOLD
        self.max_retries = MAX_RETRIES
        
        if self.provider == "gemini":
            logger.info("Using Gemini as LLM provider")
            self.model = GEMINI_MODEL
            self.api_key = GEMINI_API_KEY
        else:
            logger.info("Using Ollama as LLM provider")
            self.model = OLLAMA_MODEL
            self.api_url = OLLAMA_API
    
    def check_ollama_connection(self) -> bool:
        """
        Check if Ollama is running and accessible.
        
        Returns:
            True if connection successful, False otherwise
        """
        if self.provider == "gemini":
            # For Gemini, just check if API key is set
            return bool(self.api_key)
        
        try:
            response = requests.get(f"{self.api_url.rsplit('/api', 1)[0]}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {str(e)}")
            logger.error("   Make sure Ollama is running: 'ollama serve'")
            return False
    
    def classify_document(
        self,
        document_text: str,
        available_categories: Dict[str, str],
        filename: str = "unknown"
    ) -> Optional[Dict[str, Any]]:
        """
        Classify a document and get routing recommendation from LLM.
        
        Args:
            document_text: Extracted text content from the document
            available_categories: Dict mapping folder_path to folder_name
            filename: Original filename for context
            
        Returns:
            Classification result dictionary or None on error
        """
        # Build category description for the prompt
        categories_list = "\n".join([
            f"- {folder_name} (path: {folder_path})"
            for folder_path, folder_name in available_categories.items()
        ])
        
        # Truncate document text if too long (to avoid token limits)
        max_text_length = MAX_TEXT_LENGTH
        if len(document_text) > max_text_length:
            document_text = document_text[:max_text_length] + "\n[... document truncated ...]"
        
        # Build the user prompt
        user_prompt = f"""
Please analyze this document and classify it.

AVAILABLE CATEGORIES:
{categories_list}

DOCUMENT FILENAME: {filename}

DOCUMENT CONTENT:
{document_text}

Provide your classification in the exact JSON format requested.
"""
        
        # Prepare messages for LLM
        messages = [
            {
                "role": "system",
                "content": ROUTING_SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ]
        
        # Call LLM with retry logic
        response_text = self._call_llm(messages)
        
        if not response_text:
            return None
        
        # Parse JSON response
        try:
            result = self._parse_json_response(response_text)
            return result
        except Exception as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            logger.debug(f"Raw response: {response_text[:200]}...")
            return None
    
    def _call_llm(self, messages: list, retry_count: int = 0) -> Optional[str]:
        """
        Call LLM API (Ollama or Gemini) with retry logic.
        
        Args:
            messages: Message history for the conversation
            retry_count: Current retry attempt
            
        Returns:
            Response text from LLM or None on failure
        """
        if self.provider == "gemini":
            return self._call_gemini(messages, retry_count)
        else:
            return self._call_ollama(messages, retry_count)
    
    def _call_gemini(self, messages: list, retry_count: int = 0) -> Optional[str]:
        """
        Call Google Gemini API with retry logic.
        
        Args:
            messages: Message history for the conversation
            retry_count: Current retry attempt
            
        Returns:
            Response text from Gemini or None on failure
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=0.3,
            )
            
            # Build prompt from messages
            prompt_text = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt_text += f"System: {msg['content']}\n\n"
                else:
                    prompt_text += f"User: {msg['content']}\n\n"
            
            logger.debug(f"Calling Gemini API: {self.model}")
            response = llm.invoke(prompt_text)
            response_text = response.content
            
            # Extract string content if response is returned as a list of content blocks
            if isinstance(response_text, list):
                response_text = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in response_text])
            
            if not response_text:
                logger.error("Empty response from Gemini")
                return None
            
            return response_text
        
        except Exception as e:
            if retry_count < self.max_retries:
                logger.warning(f"Gemini error: {str(e)}, retrying...")
                import time
                time.sleep(RETRY_DELAY)
                return self._call_gemini(messages, retry_count + 1)
            else:
                logger.error(f"Gemini API error: {str(e)}")
                return None
    
    def _call_ollama(self, messages: list, retry_count: int = 0) -> Optional[str]:
        """
        Call Ollama API with retry logic.
        
        Args:
            messages: Message history for the conversation
            retry_count: Current retry attempt
            
        Returns:
            Response text from LLM or None on failure
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "temperature": 0.3,  # Low temperature for more deterministic output
            }
            
            headers = {"Content-Type": "application/json"}
            
            logger.debug(f"Calling Ollama API: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=OLLAMA_TIMEOUT
            )
            
            if response.status_code != 200:
                if retry_count < self.max_retries:
                    logger.warning(f"Ollama returned {response.status_code}, retrying...")
                    import time
                    time.sleep(RETRY_DELAY)
                    return self._call_ollama(messages, retry_count + 1)
                else:
                    logger.error(f"Ollama API error: {response.text}")
                    return None
            
            result = response.json()
            response_text = result.get("message", {}).get("content", "")
            
            if not response_text:
                logger.error("Empty response from Ollama")
                return None
            
            return response_text
        
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                logger.warning("Ollama timeout, retrying...")
                import time
                time.sleep(RETRY_DELAY)
                return self._call_ollama(messages, retry_count + 1)
            else:
                logger.error("Ollama timeout after retries")
                return None
        
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama. Is it running?")
            return None
        
        except Exception as e:
            logger.error(f"Error calling Ollama: {str(e)}")
            return None
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response (handles text wrapping and markdown).
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed dictionary or None
        """
        if not response_text or not response_text.strip():
            logger.error("Empty response from Ollama - cannot parse JSON")
            return None
        
        # Try to extract JSON from response (might be wrapped in markdown)
        text = response_text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        if not text:
            logger.error("Response became empty after removing markdown")
            return None
        
        try:
            # Parse JSON
            result = json.loads(text)
            
            # Validate required fields
            required_fields = ["confidence_score", "category_folder", "suggested_filename", "document_date"]
            for field in required_fields:
                if field not in result:
                    logger.error(f"Missing required field in JSON: {field}")
                    return None
            
            # Ensure confidence_score is numeric
            result["confidence_score"] = float(result["confidence_score"])
            
            return result
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Attempted to parse: {repr(text)}")
            return None
    
    def validate_classification(self, classification: Dict[str, Any]) -> bool:
        """
        Validate that classification meets requirements.
        
        Args:
            classification: Classification result from LLM
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check confidence is 0-100
            confidence = classification.get("confidence_score", 0)
            if not (0 <= confidence <= 100):
                logger.warning(f"Invalid confidence score: {confidence}")
                return False
            
            # Check date format
            date_str = classification.get("document_date", "")
            if not self._is_valid_date(date_str):
                logger.warning(f"Invalid date format: {date_str}")
                return False
            
            # Check other fields exist
            if not classification.get("category_folder"):
                logger.warning("Missing category_folder")
                return False
            
            if not classification.get("suggested_filename"):
                logger.warning("Missing suggested_filename")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error validating classification: {str(e)}")
            return False
    
    @staticmethod
    def _is_valid_date(date_str: str) -> bool:
        """Check if date string is in YYYY-MM-DD format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except:
            return False
