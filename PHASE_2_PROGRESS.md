# Phase 2: AI Chat - Implementation Progress

**Date**: 2025-11-06
**Status**: 50% Complete (In Progress)

## Completed ✅

### 1. Database Models
- ✅ Created `Conversation` model (`app/models/models.py:303-323`)
  - Tracks user conversations
  - Links to matter (optional scoping)
  - Supports pinning and archiving
- ✅ Created `Message` model (`app/models/models.py:326-354`)
  - Stores user and assistant messages
  - Includes source citations
  - Tracks token usage and model info
  - Supports user feedback (ratings)

### 2. Database Migration
- ✅ Generated migration: `9847e9d42908_add_conversations_and_messages_tables`
- ✅ Applied migration successfully
- ✅ Tables created in database

### 3. Pydantic Schemas
- ✅ Created comprehensive schemas (`app/schemas/chat.py`)
  - `MessageCreate`, `MessageResponse`, `MessageSource`
  - `ConversationCreate`, `ConversationUpdate`, `ConversationResponse`
  - `ConversationWithMessages`, `ConversationListResponse`
  - `ChatRequest`, `ChatResponse`
  - `ChatStreamChunk` (for SSE streaming)

### 4. Dependencies
- ✅ Installed Anthropic SDK (v0.72.0)
- ✅ Updated `requirements.txt`
- ✅ Added Claude config to `app/core/config.py`:
  - `ANTHROPIC_API_KEY`
  - `ANTHROPIC_MODEL` (claude-3-5-sonnet-20241022)
  - `ANTHROPIC_MAX_TOKENS` (4096)

## Completed (Continued) ✅

### 5. Chat Service
**Status**: ✅ Complete
**File**: `app/services/chat_service.py` (567 lines)

**Implemented Methods**:
- ✅ `send_message()` - Send message with RAG context
- ✅ `send_message_stream()` - Stream response using SSE
- ✅ `get_conversation_with_messages()` - Get conversation with history
- ✅ `list_conversations()` - List user's conversations (paginated)
- ✅ `update_conversation()` - Update title, pin, archive
- ✅ `delete_conversation()` - Delete conversation and messages
- ✅ `submit_feedback()` - Submit rating/feedback for messages

**Key Features Implemented**:
1. ✅ **RAG Context Retrieval**: Reuses existing `vector_storage_service.similarity_search()`
2. ✅ **Prompt Engineering**: Builds system prompt with document context and guidelines
3. ✅ **Claude Integration**: AsyncAnthropic client for API calls
4. ✅ **Citation Tracking**: Stores sources with document metadata in messages
5. ✅ **Message Storage**: Saves with token counts, model info, and context chunks
6. ✅ **Streaming Support**: Server-Sent Events for real-time responses

### 6. Chat CRUD Endpoints
**Status**: ✅ Complete
**File**: `app/api/v1/endpoints/chat.py` (245 lines)

**Implemented Endpoints**:
- ✅ `POST /api/v1/chat/message` - Send message, get response
- ✅ `POST /api/v1/chat/stream` - Send message, stream response (SSE)
- ✅ `GET /api/v1/chat/conversations` - List user's conversations
- ✅ `GET /api/v1/chat/conversations/{id}` - Get conversation with messages
- ✅ `PATCH /api/v1/chat/conversations/{id}` - Update conversation
- ✅ `DELETE /api/v1/chat/conversations/{id}` - Delete conversation
- ✅ `POST /api/v1/chat/messages/{id}/feedback` - Submit feedback

**Features**:
- ✅ Rate limiting (60/min for chat, 120/min for CRUD)
- ✅ Full OpenAPI documentation
- ✅ Error handling and logging
- ✅ Authentication required (all endpoints)

### 7. Router Registration
**Status**: ✅ Complete
**File**: `app/api/v1/api.py`

**Changes**:
- ✅ Imported chat router
- ✅ Registered at `/api/v1/chat` with `ai-chat` tag

## In Progress 🟡

### 8. Testing
**Status**: Test script created, pending execution
**File**: `test_chat.py`

## Remaining Tasks 📋

### 6. Chat CRUD Endpoints
**File**: `app/api/v1/endpoints/chat.py`

```python
POST   /api/v1/chat/message       # Send message, get response
POST   /api/v1/chat/stream        # Send message, stream response (SSE)
GET    /api/v1/chat/conversations # List user's conversations
GET    /api/v1/chat/conversations/{id} # Get conversation with messages
PATCH  /api/v1/chat/conversations/{id} # Update conversation (title, pin, archive)
DELETE /api/v1/chat/conversations/{id} # Delete conversation
POST   /api/v1/chat/messages/{id}/feedback # Submit rating/feedback
```

### 7. Streaming Support (SSE)
**Implementation**:
- Use FastAPI's `StreamingResponse`
- Yield chunks as Server-Sent Events
- Stream Claude's response in real-time
- Send sources after response complete

### 8. RAG Integration
**How it works**:
1. User sends message
2. Generate embedding for message (OpenAI)
3. Semantic search to find relevant chunks (existing `vector_storage_service`)
4. Build context from top chunks
5. Create system prompt with context
6. Call Claude with context + user message
7. Extract sources from Claude response
8. Save message with citations

### 9. Prompt Engineering
**System Prompt Template**:
```
You are a legal AI assistant for BC Legal Tech, helping lawyers analyze documents.

You have access to the following document excerpts that may be relevant:

<context>
{document_chunks_with_sources}
</context>

Guidelines:
- Always cite your sources using [Doc: Title, Page X]
- If you're uncertain, say "I don't know" rather than guessing
- Focus on the documents provided
- Be concise and professional
- For legal questions, remind users to verify with qualified counsel

User Question: {user_message}
```

### 10. Citation Format
**In Response**:
```
The employment agreement specifies a salary of $120,000 [Doc: Employment Agreement, Page 2].

The non-compete clause restricts employment for 12 months [Doc: Employment Agreement, Page 5].
```

**In Database** (`sources` JSON):
```json
[
  {
    "document_id": "uuid",
    "document_title": "Employment Agreement",
    "chunk_id": "uuid",
    "page_number": 2,
    "similarity_score": 0.87,
    "matter_id": "uuid",
    "matter_name": "Smith vs Acme Corp"
  }
]
```

### 11. Testing
- [ ] Create test conversation
- [ ] Send message with RAG context
- [ ] Verify sources are returned
- [ ] Test streaming endpoint
- [ ] Test feedback submission
- [ ] Test conversation listing
- [ ] Test matter scoping

## API Key Setup

Add to `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get key from: https://console.anthropic.com/

## Next Steps (Priority Order)

1. **Create Chat Service** (`app/services/chat_service.py`)
   - Implement RAG context retrieval
   - Integrate with Claude API
   - Handle citation extraction

2. **Create Chat Endpoints** (`app/api/v1/endpoints/chat.py`)
   - Basic chat endpoint (non-streaming)
   - Conversation CRUD operations

3. **Add Streaming Support**
   - Implement SSE endpoint
   - Test real-time streaming

4. **End-to-End Testing**
   - Upload document
   - Chat about document
   - Verify citations

5. **Rate Limiting**
   - Add rate limits to chat endpoints (already have infrastructure)

## Architecture Decisions

### Why Claude 3.5 Sonnet?
- Excellent at legal/professional text analysis
- Strong citation capabilities
- Good at saying "I don't know" when uncertain
- Fast enough for real-time chat
- 200K context window (plenty for RAG)

### Why Separate Conversation/Message Tables?
- Conversations are lightweight (can list many)
- Messages are heavyweight (load on demand)
- Enables conversation history without loading all messages
- Supports pagination of messages within conversation

### Why Store Sources in Message?
- Enables displaying citations without re-running search
- Audit trail of what context was used
- Can verify AI didn't hallucinate sources

## Estimated Time Remaining

- Chat Service: 2-3 hours
- Chat Endpoints: 1-2 hours
- Streaming Support: 1-2 hours
- Testing & Debugging: 2-3 hours

**Total**: 6-10 hours remaining

## Files Modified This Session

**New Files**:
- `app/models/models.py` (added Conversation, Message models)
- `app/schemas/chat.py` (all chat schemas)
- `alembic/versions/9847e9d42908_add_conversations_and_messages_tables_.py`
- `PHASE_2_PROGRESS.md` (this file)

**Modified Files**:
- `app/core/config.py` (added Anthropic settings)
- `requirements.txt` (added anthropic==0.72.0)

## Key Learnings

1. **Reuse Semantic Search**: Don't rebuild context retrieval - use existing `semantic_search` endpoint logic
2. **Citations are Critical**: For legal use case, must always cite sources
3. **Streaming Enhances UX**: Real-time response feels more interactive
4. **Matter Scoping**: Conversations can be scoped to a matter for focused search

## Questions for Next Session

1. Should we support conversation sharing between users?
2. Should we limit conversation history length (to stay within Claude context window)?
3. Should we implement conversation export (PDF/DOCX)?
4. Should chat usage count against API usage limits?
5. How should we handle conversations when documents are deleted?

---

**Status**: Core implementation complete (85%)
**Blockers**: None - Pre-existing import issues in codebase need fixing
**Next**: Fix import issues and test chat endpoints
