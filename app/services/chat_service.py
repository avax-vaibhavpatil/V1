"""
Chat Service for AI Chatbot

Orchestrates the full chatbot flow:
1. Receive user question + filters
2. Generate SQL using LLM Service
3. Validate SQL using SQL Validator
4. Execute SQL on the database
5. Format answer using LLM Service
6. Return response to user

Usage:
    from app.services.chat_service import ChatService, get_chat_service
    
    chat = get_chat_service()
    response = await chat.ask("Top 5 customers in Gujarat", filters)
"""

import time
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.logging_config import get_logger
from app.services.llm_service import LLMService, get_llm_service, LLMResponse
from app.services.sql_validator import SQLValidator, validate_sql, ValidationResult

logger = get_logger(__name__)


# =============================================================================
# Configuration
# =============================================================================

# Database connection (same as reports.py)
ANALYTICS_DB_URL = "postgresql+asyncpg://postgres:root@localhost:5430/analytics-llm"

analytics_engine = create_async_engine(
    ANALYTICS_DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AnalyticsSessionLocal = async_sessionmaker(
    analytics_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class ChatStatus(Enum):
    """Status of chat response."""
    SUCCESS = "success"
    SQL_GENERATION_FAILED = "sql_generation_failed"
    SQL_VALIDATION_FAILED = "sql_validation_failed"
    SQL_EXECUTION_FAILED = "sql_execution_failed"
    ANSWER_FORMATTING_FAILED = "answer_formatting_failed"
    NO_RESULTS = "no_results"
    ERROR = "error"


@dataclass
class ChatResponse:
    """Response from the chat service."""
    status: ChatStatus
    answer: str
    sql: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    error: Optional[str] = None
    
    # Timing info
    sql_generation_time_ms: int = 0
    sql_execution_time_ms: int = 0
    answer_formatting_time_ms: int = 0
    total_time_ms: int = 0
    
    # Token usage
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "status": self.status.value,
            "answer": self.answer,
            "sql": self.sql,
            "data": self.data,
            "rowCount": self.row_count,
            "error": self.error,
            "timing": {
                "sqlGenerationMs": self.sql_generation_time_ms,
                "sqlExecutionMs": self.sql_execution_time_ms,
                "answerFormattingMs": self.answer_formatting_time_ms,
                "totalMs": self.total_time_ms,
            },
            "usage": {
                "tokensUsed": self.tokens_used,
                "estimatedCostUsd": round(self.estimated_cost_usd, 6),
            },
            "timestamp": self.timestamp,
        }


# =============================================================================
# Chat Service
# =============================================================================

class ChatService:
    """
    Main chat service that orchestrates the full chatbot flow.
    
    Flow:
    1. User asks a question
    2. LLM generates SQL query
    3. SQL is validated for safety
    4. SQL is executed against the database
    5. Results are formatted into a natural language answer
    6. Response is returned to the user
    """
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        sql_validator: Optional[SQLValidator] = None,
        max_results: int = 100,
        query_timeout: int = 30,
    ):
        """
        Initialize the chat service.
        
        Args:
            llm_service: LLM service instance (uses default if None)
            sql_validator: SQL validator instance (uses default if None)
            max_results: Maximum rows to return from query
            query_timeout: Query timeout in seconds
        """
        self.llm = llm_service or get_llm_service()
        self.validator = sql_validator or SQLValidator()
        self.max_results = max_results
        self.query_timeout = query_timeout
        
        # Statistics
        self.total_questions = 0
        self.successful_questions = 0
        self.failed_questions = 0
        
        logger.info("ChatService initialized")
    
    # =========================================================================
    # Main API
    # =========================================================================
    
    async def ask(
        self,
        question: str,
        filters: Optional[Dict] = None,
        include_sql: bool = True,
        include_data: bool = True,
    ) -> ChatResponse:
        """
        Ask a question and get an answer.
        
        This is the main entry point for the chatbot.
        
        Args:
            question: User's natural language question
            filters: Current dashboard filters (optional)
            include_sql: Whether to include SQL in response
            include_data: Whether to include raw data in response
            
        Returns:
            ChatResponse with answer, SQL, data, and metadata
        """
        start_time = time.time()
        self.total_questions += 1
        
        total_tokens = 0
        total_cost = 0.0
        
        logger.info(f"Processing question: {question[:100]}...")
        
        # =====================================================================
        # Step 1: Generate SQL
        # =====================================================================
        sql_start = time.time()
        
        try:
            sql_response = await self.llm.generate_sql(question, filters)
            
            if not sql_response.success:
                self.failed_questions += 1
                return ChatResponse(
                    status=ChatStatus.SQL_GENERATION_FAILED,
                    answer=f"I couldn't understand your question. {sql_response.error or 'Please try rephrasing.'}",
                    error=sql_response.error,
                    sql_generation_time_ms=int((time.time() - sql_start) * 1000),
                    total_time_ms=int((time.time() - start_time) * 1000),
                )
            
            sql = sql_response.content
            total_tokens += sql_response.total_tokens
            total_cost += sql_response.cost_estimate
            
        except Exception as e:
            logger.error(f"SQL generation error: {e}", exc_info=True)
            self.failed_questions += 1
            return ChatResponse(
                status=ChatStatus.SQL_GENERATION_FAILED,
                answer="Sorry, I encountered an error while processing your question. Please try again.",
                error=str(e),
                total_time_ms=int((time.time() - start_time) * 1000),
            )
        
        sql_gen_time = int((time.time() - sql_start) * 1000)
        logger.info(f"SQL generated in {sql_gen_time}ms: {sql[:100]}...")
        
        # =====================================================================
        # Step 2: Validate SQL
        # =====================================================================
        validation_result = self.validator.validate(sql)
        
        if not validation_result.is_valid:
            logger.warning(f"SQL validation failed: {validation_result.error_message}")
            self.failed_questions += 1
            return ChatResponse(
                status=ChatStatus.SQL_VALIDATION_FAILED,
                answer="I generated a query but it didn't pass safety checks. Please try a different question.",
                sql=sql if include_sql else None,
                error=validation_result.error_message,
                sql_generation_time_ms=sql_gen_time,
                total_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=total_tokens,
                estimated_cost_usd=total_cost,
            )
        
        # Use sanitized SQL
        sql = validation_result.sanitized_sql or sql
        
        # =====================================================================
        # Step 3: Execute SQL
        # =====================================================================
        exec_start = time.time()
        
        try:
            results = await self._execute_query(sql)
            row_count = len(results)
            
        except Exception as e:
            logger.error(f"SQL execution error: {e}", exc_info=True)
            self.failed_questions += 1
            return ChatResponse(
                status=ChatStatus.SQL_EXECUTION_FAILED,
                answer="I couldn't retrieve the data. The query might be invalid or the data might not exist.",
                sql=sql if include_sql else None,
                error=str(e),
                sql_generation_time_ms=sql_gen_time,
                sql_execution_time_ms=int((time.time() - exec_start) * 1000),
                total_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=total_tokens,
                estimated_cost_usd=total_cost,
            )
        
        sql_exec_time = int((time.time() - exec_start) * 1000)
        logger.info(f"SQL executed in {sql_exec_time}ms, {row_count} rows returned")
        
        # =====================================================================
        # Step 4: Handle No Results
        # =====================================================================
        if row_count == 0:
            self.successful_questions += 1
            return ChatResponse(
                status=ChatStatus.NO_RESULTS,
                answer="I didn't find any data matching your query. This could mean:\n"
                       "• No transactions exist for the specified criteria\n"
                       "• The filters might be too restrictive\n"
                       "Try broadening your search or changing the filters.",
                sql=sql if include_sql else None,
                data=[] if include_data else None,
                row_count=0,
                sql_generation_time_ms=sql_gen_time,
                sql_execution_time_ms=sql_exec_time,
                total_time_ms=int((time.time() - start_time) * 1000),
                tokens_used=total_tokens,
                estimated_cost_usd=total_cost,
            )
        
        # =====================================================================
        # Step 5: Format Answer
        # =====================================================================
        format_start = time.time()
        
        try:
            # Limit results for formatting to avoid token overflow
            results_for_formatting = results[:20] if len(results) > 20 else results
            
            answer_response = await self.llm.format_answer(
                question=question,
                sql=sql,
                results=results_for_formatting,
            )
            
            if answer_response.success:
                answer = answer_response.content
                total_tokens += answer_response.total_tokens
                total_cost += answer_response.cost_estimate
            else:
                # Fallback to simple formatting
                answer = self._simple_format(question, results)
            
        except Exception as e:
            logger.error(f"Answer formatting error: {e}", exc_info=True)
            # Fallback to simple formatting
            answer = self._simple_format(question, results)
        
        format_time = int((time.time() - format_start) * 1000)
        total_time = int((time.time() - start_time) * 1000)
        
        self.successful_questions += 1
        logger.info(f"Question answered successfully in {total_time}ms")
        
        return ChatResponse(
            status=ChatStatus.SUCCESS,
            answer=answer,
            sql=sql if include_sql else None,
            data=results if include_data else None,
            row_count=row_count,
            sql_generation_time_ms=sql_gen_time,
            sql_execution_time_ms=sql_exec_time,
            answer_formatting_time_ms=format_time,
            total_time_ms=total_time,
            tokens_used=total_tokens,
            estimated_cost_usd=total_cost,
        )
    
    # =========================================================================
    # Internal Methods
    # =========================================================================
    
    async def _execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query against the analytics database.
        
        Args:
            sql: SQL query string
            
        Returns:
            List of result rows as dictionaries
        """
        # Add LIMIT if not present to prevent runaway queries
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {self.max_results}"
        
        async with AnalyticsSessionLocal() as session:
            result = await session.execute(text(sql))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to list of dicts, handling special types
            data = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    # Convert Decimal and other types to float/str
                    if val is None:
                        row_dict[col] = None
                    elif isinstance(val, (int, float, str, bool)):
                        row_dict[col] = val
                    else:
                        # Try to convert to float, fallback to string
                        try:
                            row_dict[col] = float(val)
                        except (TypeError, ValueError):
                            row_dict[col] = str(val)
                data.append(row_dict)
            
            return data
    
    def _simple_format(self, question: str, results: List[Dict]) -> str:
        """
        Simple fallback formatting when LLM formatting fails.
        
        Args:
            question: Original question
            results: Query results
            
        Returns:
            Formatted answer string
        """
        if not results:
            return "No results found."
        
        # Get column names
        columns = list(results[0].keys())
        
        # Build simple response
        lines = [f"Found {len(results)} results:\n"]
        
        for i, row in enumerate(results[:10], 1):
            row_parts = []
            for col in columns:
                val = row.get(col)
                if isinstance(val, (int, float)) and val > 1000:
                    val = f"{val:,.2f}"
                row_parts.append(f"{col}: {val}")
            lines.append(f"{i}. {', '.join(row_parts)}")
        
        if len(results) > 10:
            lines.append(f"\n... and {len(results) - 10} more rows")
        
        return "\n".join(lines)
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        success_rate = (
            (self.successful_questions / self.total_questions * 100)
            if self.total_questions > 0 else 0
        )
        
        return {
            "total_questions": self.total_questions,
            "successful_questions": self.successful_questions,
            "failed_questions": self.failed_questions,
            "success_rate_percent": round(success_rate, 1),
            "llm_usage": self.llm.get_usage_stats(),
        }
    
    def reset_stats(self):
        """Reset service statistics."""
        self.total_questions = 0
        self.successful_questions = 0
        self.failed_questions = 0
        self.llm.reset_usage_stats()
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all components."""
        health = {
            "llm_service": False,
            "database": False,
            "overall": False,
        }
        
        # Check LLM
        try:
            health["llm_service"] = await self.llm.health_check()
        except Exception:
            pass
        
        # Check database
        try:
            async with AnalyticsSessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                health["database"] = result.scalar() == 1
        except Exception:
            pass
        
        health["overall"] = health["llm_service"] and health["database"]
        
        return health


# =============================================================================
# Singleton Instance
# =============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get the singleton chat service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


async def ask(question: str, filters: Optional[Dict] = None) -> ChatResponse:
    """
    Quick function to ask a question.
    
    Returns ChatResponse.
    """
    service = get_chat_service()
    return await service.ask(question, filters)


