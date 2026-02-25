# Query History & Token Usage Feature - Implementation Plan

## Overview
This feature will allow users to view their query history and token usage from the `metadata.llm_metadata` database table. The feature will be integrated into the existing UI without colliding with the current frontend structure.

## Database Schema Analysis
Based on the `llm_metadata` table structure, we have access to:
- `user_question` - The query/question asked by the user
- `chatbot_answer` - The response from the chatbot
- `response_time_ms` - Response time in milliseconds
- `tokens_used` - Number of tokens consumed
- `sql_generated` - The SQL query generated
- `status` - Status of the query (success/error)
- `error_message` - Error message if any
- `row_count` - Number of rows returned
- `estimated_cost_usd` - Estimated cost in USD
- `report_id` - Report identifier
- `filters_applied` - JSONB field with applied filters
- `created_at` - Timestamp (assumed, needs verification)

## Architecture Plan

### 1. Backend Implementation

#### 1.1 Service Layer (`app/services/llm_metadata_service.py`)
- **Purpose**: Handle database queries to fetch LLM metadata
- **Methods**:
  - `list_metadata()` - Get paginated list of queries with filters
  - `get_metadata_by_id()` - Get specific query details
  - `get_token_statistics()` - Get aggregated token usage stats
- **Database Connection**: Use `AnalyticsSessionLocal` (same as chat_service.py)
- **Features**:
  - Pagination support (skip/limit)
  - Filtering by report_id, date range, status
  - Sorting by created_at (newest first)
  - Token usage aggregation

#### 1.2 API Endpoint (`app/api/v1/llm_metadata.py`)
- **Route**: `/api/v1/llm-metadata`
- **Endpoints**:
  - `GET /api/v1/llm-metadata` - List queries with pagination
    - Query params: `skip`, `limit`, `report_id`, `start_date`, `end_date`, `status`
  - `GET /api/v1/llm-metadata/{id}` - Get specific query details
  - `GET /api/v1/llm-metadata/stats` - Get token usage statistics
- **Authentication**: Use `RequireRead` dependency (same as other endpoints)
- **Response Models**: Pydantic models for request/response

#### 1.3 Router Registration
- Add router to `app/api/v1/__init__.py`
- Tag: `["llm-metadata"]`

### 2. Frontend Implementation

#### 2.1 TypeScript Types (`frontend/src/types/index.ts`)
- Add `LLMMetadata` interface matching the database schema
- Add `LLMMetadataStats` interface for aggregated statistics
- Add query parameters interface

#### 2.2 API Service (`frontend/src/services/llmMetadata.ts`)
- Create service following the pattern of `datasets.ts`
- Methods:
  - `list()` - Fetch paginated query history
  - `get()` - Get specific query details
  - `getStats()` - Get token usage statistics

#### 2.3 UI Component (`frontend/src/pages/QueryHistoryPage.tsx`)
- **Layout**: Follow the pattern of `DatasetsPage.tsx`
- **Features**:
  - Table view of query history with columns:
    - Timestamp
    - User Question (truncated with expand option)
    - Status (badge)
    - Tokens Used
    - Cost (USD)
    - Response Time (ms)
    - Actions (View Details)
  - Filters:
    - Date range picker
    - Report ID filter
    - Status filter
  - Statistics Panel:
    - Total queries
    - Total tokens used
    - Average tokens per query
    - Total cost
    - Average response time
  - Pagination controls
  - Expandable row details showing:
    - Full question
    - Full answer
    - Generated SQL
    - Filters applied
    - Error message (if any)

#### 2.4 Routing & Navigation
- **Route**: `/query-history` (add to `App.tsx`)
- **Sidebar**: Add to "Analytics" section with icon (MessageSquare or History)
- **Icon**: Use `lucide-react` icon (e.g., `MessageSquare` or `History`)

### 3. UI/UX Considerations

#### 3.1 Design Consistency
- Follow existing design patterns from `DatasetsPage.tsx`
- Use same color scheme and spacing
- Match button styles and modal patterns

#### 3.2 Performance
- Implement pagination (default: 20 items per page)
- Lazy load details on expand
- Cache statistics for better performance

#### 3.3 User Experience
- Clear visual indicators for status (success/error)
- Token usage displayed with formatting (e.g., "1,234 tokens")
- Cost displayed with currency formatting
- Responsive design for mobile/tablet
- Loading states and error handling

### 4. File Structure

```
Backend:
├── app/
│   ├── api/v1/
│   │   └── llm_metadata.py (NEW)
│   └── services/
│       └── llm_metadata_service.py (NEW)

Frontend:
├── frontend/src/
│   ├── pages/
│   │   └── QueryHistoryPage.tsx (NEW)
│   ├── services/
│   │   └── llmMetadata.ts (NEW)
│   └── types/
│       └── index.ts (UPDATE)
```

### 5. Implementation Steps

1. ✅ **Plan** - Create this planning document
2. **Backend Service** - Create `llm_metadata_service.py`
3. **Backend API** - Create `llm_metadata.py` endpoint
4. **Router Registration** - Add to API router
5. **Frontend Types** - Add TypeScript interfaces
6. **Frontend Service** - Create API service
7. **Frontend Page** - Create QueryHistoryPage component
8. **Routing** - Add route and sidebar navigation
9. **Testing** - Test with real data from database

### 6. Potential Enhancements (Future)
- Export query history to CSV
- Search functionality
- Filter by token usage range
- Cost alerts/thresholds
- Query performance analytics
- Most common queries report

## Notes
- The feature will use the existing authentication/authorization system
- Database connection uses the same `AnalyticsSessionLocal` pattern
- UI will be consistent with existing pages
- No breaking changes to existing functionality


