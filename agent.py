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
        
        # Call LLM and parse with retry logic on both network and parsing failures
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                logger.info(f"🔄 Retrying classification (Attempt {attempt + 1}/{self.max_retries + 1})...")
            
            response_text = self._call_llm(messages)
            
            if not response_text:
                if attempt < self.max_retries:
                    import time
                    time.sleep(RETRY_DELAY)
                    continue
                return None
            
            # Parse JSON response
            try:
                result = self._parse_json_response(response_text)
                if result:
                    return result
            except Exception as e:
                logger.error(f"Error parsing LLM response: {str(e)}")
                logger.debug(f"Raw response: {response_text[:200]}...")
            
            if attempt < self.max_retries:
                import time
                time.sleep(RETRY_DELAY)
        
        logger.error(f"Failed to classify document after {self.max_retries + 1} attempts")
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
                "format": "json"
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
    
    @staticmethod
    def _standardize_date(date_str: str) -> str:
        """
        Attempt to parse and standardize date string to YYYY-MM-DD.
        If parsing fails, returns the original string.
        """
        date_str = date_str.strip()
        formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%m-%d-%Y",
            "%Y/%m/%d",
            "%d/%m/%Y",
            "%m/%d/%Y",
            "%Y.%m.%d",
            "%d.%m.%Y",
            "%d %B, %Y",
            "%d %b, %Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y",
            "%B %d %Y",
            "%b %d %Y",
            "%Y %B %d",
            "%Y %b %d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        # If it is just a year (e.g. "2026")
        if len(date_str) == 4 and date_str.isdigit():
            return f"{date_str}-01-01"
        
        return date_str

    @staticmethod
    def _clean_json_comments(json_str: str) -> str:
        """
        Strip line and trailing comments starting with // or # from a JSON string,
        while preserving them if they occur inside double-quoted strings or URLs.
        """
        cleaned_lines = []
        for line in json_str.splitlines():
            comment_idx = -1
            in_quote = False
            i = 0
            while i < len(line):
                char = line[i]
                if char == '"':
                    # Ignore escaped quotes
                    if i > 0 and line[i-1] == '\\':
                        pass
                    else:
                        in_quote = not in_quote
                elif not in_quote:
                    if char == '#' or (char == '/' and i + 1 < len(line) and line[i+1] == '/'):
                        prefix = line[:i]
                        if not (prefix.endswith("http:") or prefix.endswith("https:")):
                            comment_idx = i
                            break
                i += 1
            
            if comment_idx != -1:
                cleaned_line = line[:comment_idx].rstrip()
            else:
                cleaned_line = line
            cleaned_lines.append(cleaned_line)
        return "\n".join(cleaned_lines)

    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response (handles text wrapping, surrounding conversation, and markdown).
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed dictionary or None
        """
        if not response_text or not response_text.strip():
            logger.error("Empty response from LLM - cannot parse JSON")
            return None
        
        # Try to find the JSON block using '{' and '}'
        # This is more robust against conversation surrounding the JSON block
        text = response_text.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            text = text[start_idx:end_idx + 1]
        else:
            # Fallback to removing markdown code blocks if present
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        
        if not text:
            logger.error("Response became empty after removing markdown / extraction")
            return None
        
        # Clean inline/line comments before parsing
        text = self._clean_json_comments(text)
        
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
            
            # Standardize date format to YYYY-MM-DD
            result["document_date"] = self._standardize_date(result["document_date"])
            
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
