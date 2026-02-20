"""
LLM Service for AI Chatbot

Handles communication with OpenAI API for:
1. SQL Generation - Convert natural language to SQL
2. Answer Formatting - Convert query results to human-readable responses

Usage:
    from app.services.llm_service import LLMService, get_llm_service
    
    llm = get_llm_service()
    
    # Generate SQL
    sql = await llm.generate_sql(question, filters)
    
    # Format answer
    answer = await llm.format_answer(question, sql, results)
"""

import os
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from openai import AsyncOpenAI
from openai import OpenAIError, APIError, RateLimitError, APIConnectionError

from app.core.logging_config import get_logger
from app.semantic.llm_prompts import (
    build_complete_prompt,
    format_answer_prompt,
    get_error_response,
    EXAMPLE_QA_PAIRS,
)
from app.semantic.stock_llm_prompts import (
    build_complete_prompt_stock,
    format_answer_prompt_stock,
)

logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

class LLMModel(Enum):
    """Available LLM models."""
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_35_TURBO = "gpt-3.5-turbo"


@dataclass
class LLMConfig:
    """Configuration for LLM service."""
    api_key: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.1  # Low temperature for consistent SQL
    max_tokens_sql: int = 500  # SQL queries are short
    max_tokens_answer: int = 500  # Answers should be concise
    timeout: float = 30.0  # Request timeout in seconds
    max_retries: int = 2


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    success: bool
    error: Optional[str] = None
    
    @property
    def cost_estimate(self) -> float:
        """Estimate cost in USD (GPT-4o-mini pricing)."""
        # GPT-4o-mini: $0.15/1M input, $0.60/1M output
        input_cost = (self.prompt_tokens / 1_000_000) * 0.15
        output_cost = (self.completion_tokens / 1_000_000) * 0.60
        return input_cost + output_cost


# =============================================================================
# LLM Service
# =============================================================================

class LLMService:
    """
    Service for interacting with OpenAI's LLM API.
    
    Features:
    - Async API calls for better performance
    - Automatic retry on rate limits
    - Token usage tracking
    - Cost estimation
    - Error handling with user-friendly messages
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM service.
        
        Args:
            config: LLM configuration. If None, loads from environment.
        """
        if config:
            self.config = config
        else:
            # Load from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            
            self.config = LLMConfig(
                api_key=api_key,
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            )
        
        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries,
        )
        
        # Track usage
        self.total_tokens_used = 0
        self.total_requests = 0
        
        logger.info(f"LLMService initialized with model: {self.config.model}")
    
    # =========================================================================
    # SQL Generation
    # =========================================================================
    
    async def generate_sql(
        self,
        question: str,
        filters: Optional[Dict] = None,
        include_examples: int = 5,
        report_id: str = "sales-analytics",
    ) -> LLMResponse:
        """
        Generate SQL query from natural language question.

        Args:
            question: User's natural language question
            filters: Current dashboard filters (optional)
            include_examples: Number of few-shot examples to include
            report_id: Report context - "sales-analytics" or "stock-inventory"

        Returns:
            LLMResponse with generated SQL in content field
        """
        logger.info(f"Generating SQL for report={report_id}: {question[:100]}...")

        # Build prompts using the semantic layer for the active report
        if report_id == "stock-inventory":
            system_prompt, user_prompt = build_complete_prompt_stock(
                question=question,
                filters=filters,
                include_examples=include_examples,
            )
        else:
            system_prompt, user_prompt = build_complete_prompt(
                question=question,
                filters=filters,
                include_examples=include_examples,
            )
        
        # Call LLM
        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=self.config.max_tokens_sql,
            temperature=0.1,  # Low temperature for consistent SQL
        )
        
        if response.success:
            # Clean up the SQL response
            sql = self._clean_sql_response(response.content)
            response.content = sql
            logger.info(f"SQL generated successfully: {sql[:100]}...")
        else:
            logger.error(f"SQL generation failed: {response.error}")
        
        return response
    
    # =========================================================================
    # Answer Formatting
    # =========================================================================
    
    async def format_answer(
        self,
        question: str,
        sql: str,
        results: Any,
        report_id: str = "sales-analytics",
    ) -> LLMResponse:
        """
        Format query results into a human-readable answer.

        Args:
            question: Original user question
            sql: SQL query that was executed
            results: Query results (list of dicts)
            report_id: Report context for answer tone (sales vs stock)

        Returns:
            LLMResponse with formatted answer in content field
        """
        logger.info(f"Formatting answer for report={report_id}: {question[:50]}...")

        if report_id == "stock-inventory":
            user_prompt = format_answer_prompt_stock(question, sql, results)
            system_prompt = """You are a helpful stock inventory assistant.
Format query results into clear, conversational responses.
Use ₹ for currency, format large numbers with commas.
Refer to stock/inventory data, not sales analytics. Be concise."""
        else:
            user_prompt = format_answer_prompt(question, sql, results)
            system_prompt = """You are a helpful sales analytics assistant.
Format query results into clear, conversational responses.
Use ₹ for currency, format large numbers with commas.
Be concise but informative. Use bullet points for lists.
If no results, explain what that means."""
        
        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=self.config.max_tokens_answer,
            temperature=0.3,  # Slightly higher for natural language
        )
        
        return response
    
    # =========================================================================
    # Quick Question Classification
    # =========================================================================
    
    async def classify_question(self, question: str) -> Dict[str, Any]:
        """
        Classify question type and extract key entities.
        
        This is a lighter call to understand the question before full SQL generation.
        Can be used for routing or validation.
        
        Args:
            question: User's question
            
        Returns:
            Dict with classification info
        """
        system_prompt = """Classify this analytics question. Return JSON only:
{
    "intent": "ranking|aggregation|comparison|trend|filter|other",
    "entities": ["customer", "product", etc],
    "measures": ["sales", "profit", etc],
    "has_filter": true/false,
    "is_answerable": true/false
}"""
        
        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=question,
            max_tokens=100,
            temperature=0,
        )
        
        if response.success:
            try:
                import json
                return json.loads(response.content)
            except json.JSONDecodeError:
                return {"intent": "other", "is_answerable": True}
        
        return {"intent": "other", "is_answerable": True}
    
    # =========================================================================
    # Internal Methods
    # =========================================================================
    
    async def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> LLMResponse:
        """
        Make API call to OpenAI.
        
        Args:
            system_prompt: System message
            user_prompt: User message
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-1)
            
        Returns:
            LLMResponse object
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            # Extract response data
            content = response.choices[0].message.content or ""
            usage = response.usage
            
            # Update tracking
            self.total_tokens_used += usage.total_tokens
            self.total_requests += 1
            
            logger.debug(
                f"LLM call successful. Tokens: {usage.total_tokens} "
                f"(prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})"
            )
            
            return LLMResponse(
                content=content,
                model=response.model,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                success=True,
            )
            
        except RateLimitError as e:
            logger.error(f"Rate limit error: {e}")
            return LLMResponse(
                content="",
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                success=False,
                error="Rate limit exceeded. Please try again in a moment.",
            )
            
        except APIConnectionError as e:
            logger.error(f"Connection error: {e}")
            return LLMResponse(
                content="",
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                success=False,
                error="Unable to connect to AI service. Please check your connection.",
            )
            
        except APIError as e:
            logger.error(f"API error: {e}")
            return LLMResponse(
                content="",
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                success=False,
                error=f"AI service error: {str(e)}",
            )
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            return LLMResponse(
                content="",
                model=self.config.model,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                success=False,
                error="An unexpected error occurred. Please try again.",
            )
    
    def _clean_sql_response(self, content: str) -> str:
        """
        Clean up LLM-generated SQL response.
        
        Removes markdown code blocks, extra whitespace, etc.
        """
        sql = content.strip()
        
        # Remove markdown code blocks
        if sql.startswith("```sql"):
            sql = sql[6:]
        elif sql.startswith("```"):
            sql = sql[3:]
        
        if sql.endswith("```"):
            sql = sql[:-3]
        
        # Clean up whitespace
        sql = sql.strip()
        
        # Remove any explanation text (keep only SQL)
        # If there's text after the SQL, try to extract just the query
        if "SELECT" in sql.upper():
            # Find the SQL query
            import re
            match = re.search(
                r'(SELECT\s+.*?)(?:;|$)', 
                sql, 
                re.IGNORECASE | re.DOTALL
            )
            if match:
                sql = match.group(1).strip()
        
        return sql
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens_used,
            "estimated_cost_usd": (self.total_tokens_used / 1_000_000) * 0.375,  # Avg of input/output
            "model": self.config.model,
        }
    
    def reset_usage_stats(self):
        """Reset usage tracking."""
        self.total_tokens_used = 0
        self.total_requests = 0
    
    async def health_check(self) -> bool:
        """Check if LLM service is operational."""
        try:
            response = await self._call_llm(
                system_prompt="Respond with OK",
                user_prompt="Health check",
                max_tokens=5,
                temperature=0,
            )
            return response.success
        except Exception:
            return False


# =============================================================================
# Singleton Instance
# =============================================================================

_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the singleton LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def generate_sql(question: str, filters: Optional[Dict] = None) -> str:
    """
    Quick function to generate SQL from a question.
    
    Returns SQL string or raises exception on error.
    """
    service = get_llm_service()
    response = await service.generate_sql(question, filters)
    
    if not response.success:
        raise Exception(response.error)
    
    return response.content


async def format_answer(question: str, sql: str, results: Any) -> str:
    """
    Quick function to format query results.
    
    Returns formatted answer string or raises exception on error.
    """
    service = get_llm_service()
    response = await service.format_answer(question, sql, results)
    
    if not response.success:
        raise Exception(response.error)
    
    return response.content


