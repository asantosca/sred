# Chat Mode Redesign - Implementation Plan

**Status: IMPLEMENTED**

## Overview

Redesign the chat functionality to support three distinct modes:
1. **Help Desk** - Platform assistance (separate small modal)
2. **AI Discovery** - General legal AI without RAG (no matter selected)
3. **Matter Chat** - Document-focused RAG chat (matter selected)

Key feature: AI Discovery mode detects when a question relates to a user's matter and offers to link the conversation.

---

## Phase 1: Remove "All Matters" Option

### 1.1 Update MatterSelectorCompact
**File**: `frontend/src/components/chat/MatterSelectorCompact.tsx`

Changes:
- Change default option from "All documents (no matter filter)" to "AI Discovery (no documents)"
- Update placeholder text to clarify behavior
- Keep the X button to clear selection (returns to Discovery mode)

```tsx
// Before
<option value="">All documents (no matter filter)</option>

// After
<option value="">AI Discovery (general assistance)</option>
```

### 1.2 Update ChatPage Placeholder Text
**File**: `frontend/src/pages/ChatPage.tsx`

Update the `MessageInput` placeholder to reflect the new modes:
- No matter: "Ask a general legal question..."
- Matter selected: "Ask about documents in this matter..."

### 1.3 Update Conversation Header Badge
**File**: `frontend/src/pages/ChatPage.tsx` (lines 276-279)

Change "All documents" badge to "AI Discovery" badge with different styling.

---

## Phase 2: Backend - Discovery Mode (No RAG)

### 2.1 Modify _retrieve_context
**File**: `backend/app/services/chat_service.py`

When `matter_id` is `None`, skip RAG retrieval entirely:

```python
async def _retrieve_context(self, query, matter_id, ...):
    # Discovery mode - no RAG
    if matter_id is None:
        return [], []

    # Existing RAG logic for matter-scoped search...
```

### 2.2 Update System Prompt for Discovery Mode
**File**: `backend/app/services/chat_service.py`

Add a new system prompt variant for Discovery mode:

```python
def _build_system_prompt(self, context_chunks, is_discovery_mode=False):
    if is_discovery_mode:
        return """You are a legal AI assistant for BC Legal Tech.

You are in Discovery mode - answering general legal questions without
searching the user's documents.

Guidelines:
- Answer general legal questions using your knowledge
- Be helpful with BC legal procedures, terminology, and concepts
- If the user asks about specific documents or cases, suggest they
  select a matter to search their documents
- Be concise and professional
- Remind users to verify with qualified counsel for legal advice"""

    # Existing context-based prompt...
```

### 2.3 Pass Discovery Mode Flag
Update `send_message` and `send_message_stream` to pass the flag:

```python
is_discovery_mode = conversation.matter_id is None
system_prompt = self._build_system_prompt(context_chunks, is_discovery_mode)
```

---

## Phase 3: Matter Detection and Linking

### 3.1 Add Matter Detection Service Method
**File**: `backend/app/services/chat_service.py`

New method to detect if a query relates to any matter:

```python
async def _detect_related_matter(
    self,
    query: str,
    user: User,
    threshold: float = 0.7
) -> Optional[Dict[str, Any]]:
    """
    Check if the user's query semantically matches documents in any matter.
    Returns the best matching matter if similarity exceeds threshold.
    """
    query_embedding = embedding_service.generate_embedding(query)
    if not query_embedding:
        return None

    # Search across ALL user's matters (no matter_id filter)
    results = await vector_storage_service.similarity_search(
        query_embedding=query_embedding,
        company_id=user.company_id,
        matter_id=None,  # Search all
        limit=3,
        similarity_threshold=threshold
    )

    if not results:
        return None

    # Get the matter with highest similarity
    top_result = results[0]
    doc_query = select(Document, Matter).join(Matter).where(
        Document.id == top_result["document_id"]
    )
    doc_result = await self.db.execute(doc_query)
    doc_matter = doc_result.first()

    if doc_matter:
        doc, matter = doc_matter
        return {
            "matter_id": matter.id,
            "matter_name": f"{matter.matter_number} - {matter.client_name}",
            "similarity": top_result["similarity"],
            "matched_document": doc.document_title or doc.filename
        }

    return None
```

### 3.2 Integrate Detection into Streaming Response
**File**: `backend/app/services/chat_service.py`

In `send_message_stream`, after generating the response in Discovery mode:

```python
# After streaming complete, check for matter relevance (Discovery mode only)
if conversation.matter_id is None:
    suggested_matter = await self._detect_related_matter(
        query=request.message,
        user=current_user,
        threshold=0.7
    )
    if suggested_matter:
        yield f"data: {self._format_sse_chunk('matter_suggestion', suggested_matter)}\n\n"
```

### 3.3 Update ChatStreamChunk Schema
**File**: `backend/app/schemas/chat.py`

Add new chunk type for matter suggestions:

```python
class MatterSuggestion(BaseModel):
    """Suggested matter based on query relevance"""
    matter_id: UUID
    matter_name: str
    similarity: float
    matched_document: str

class ChatStreamChunk(BaseModel):
    type: str = Field(..., pattern="^(content|source|done|error|matter_suggestion)$")
    # ... existing fields ...
    matter_suggestion: Optional[MatterSuggestion] = None
```

### 3.4 Add Conversation Update Endpoint for Matter Linking
**File**: `backend/app/api/v1/endpoints/chat.py`

Add endpoint to link a conversation to a matter:

```python
@router.post("/conversations/{conversation_id}/link-matter")
async def link_conversation_to_matter(
    conversation_id: UUID,
    matter_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Link an existing conversation to a matter"""
    service = ChatService(db)
    conversation = await service.link_to_matter(
        conversation_id=conversation_id,
        matter_id=matter_id,
        current_user=current_user
    )
    return {"success": True, "matter_name": conversation.matter_name}
```

### 3.5 Add link_to_matter Service Method
**File**: `backend/app/services/chat_service.py`

```python
async def link_to_matter(
    self,
    conversation_id: UUID,
    matter_id: UUID,
    current_user: User
) -> Conversation:
    """Link a conversation to a matter and update title"""
    conversation = await self._get_conversation(conversation_id, current_user)

    # Verify user has access to the matter
    matter_query = select(Matter).where(
        and_(
            Matter.id == matter_id,
            Matter.company_id == current_user.company_id
        )
    )
    matter_result = await self.db.execute(matter_query)
    matter = matter_result.scalar()

    if not matter:
        raise ValueError("Matter not found or access denied")

    # Update conversation
    conversation.matter_id = matter_id

    # Update title to include matter name
    if not conversation.title.startswith("["):
        conversation.title = f"[{matter.client_name}] {conversation.title}"

    conversation.updated_at = datetime.utcnow()
    await self.db.commit()
    await self.db.refresh(conversation)

    return conversation
```

---

## Phase 4: Frontend - Matter Suggestion UI

### 4.1 Update Chat Types
**File**: `frontend/src/types/chat.ts`

```typescript
export interface MatterSuggestion {
  matter_id: string
  matter_name: string
  similarity: number
  matched_document: string
}

export interface ChatStreamChunk {
  type: 'content' | 'source' | 'done' | 'error' | 'matter_suggestion'
  content?: string
  source?: MessageSource
  message_id?: string
  conversation_id?: string
  error?: string
  matter_suggestion?: MatterSuggestion
}
```

### 4.2 Add API Method for Linking
**File**: `frontend/src/lib/api.ts`

```typescript
linkConversationToMatter: (conversationId: string, matterId: string) =>
  api.post(`/chat/conversations/${conversationId}/link-matter`, { matter_id: matterId })
```

### 4.3 Create MatterSuggestionBanner Component
**File**: `frontend/src/components/chat/MatterSuggestionBanner.tsx`

```tsx
interface MatterSuggestionBannerProps {
  suggestion: MatterSuggestion
  onAccept: () => void
  onDismiss: () => void
  loading?: boolean
}

export default function MatterSuggestionBanner({
  suggestion,
  onAccept,
  onDismiss,
  loading
}: MatterSuggestionBannerProps) {
  return (
    <div className="mx-4 my-2 rounded-lg border border-blue-200 bg-blue-50 p-3">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-2">
          <Briefcase className="mt-0.5 h-4 w-4 text-blue-600" />
          <div>
            <p className="text-sm font-medium text-blue-900">
              This may relate to: {suggestion.matter_name}
            </p>
            <p className="text-xs text-blue-700">
              Matched document: {suggestion.matched_document}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="primary" onClick={onAccept} disabled={loading}>
            {loading ? 'Linking...' : 'Link to Matter'}
          </Button>
          <Button size="sm" variant="ghost" onClick={onDismiss}>
            Dismiss
          </Button>
        </div>
      </div>
    </div>
  )
}
```

### 4.4 Integrate into ChatPage
**File**: `frontend/src/pages/ChatPage.tsx`

Add state and handlers:

```tsx
const [matterSuggestion, setMatterSuggestion] = useState<MatterSuggestion | null>(null)
const [isLinking, setIsLinking] = useState(false)

// In handleSendMessage, handle matter_suggestion chunk:
else if (parsed.type === 'matter_suggestion' && parsed.matter_suggestion) {
  setMatterSuggestion(parsed.matter_suggestion)
}

// Handler for accepting suggestion
const handleAcceptMatterSuggestion = async () => {
  if (!matterSuggestion || !selectedConversationId) return

  setIsLinking(true)
  try {
    await chatApi.linkConversationToMatter(
      selectedConversationId,
      matterSuggestion.matter_id
    )
    setSelectedMatterId(matterSuggestion.matter_id)
    setMatterSuggestion(null)
    queryClient.invalidateQueries({ queryKey: ['conversation', selectedConversationId] })
    toast.success(`Linked to ${matterSuggestion.matter_name}`)
  } catch (err) {
    toast.error('Failed to link conversation')
  } finally {
    setIsLinking(false)
  }
}

// Render banner after ChatInterface if suggestion exists
{matterSuggestion && (
  <MatterSuggestionBanner
    suggestion={matterSuggestion}
    onAccept={handleAcceptMatterSuggestion}
    onDismiss={() => setMatterSuggestion(null)}
    loading={isLinking}
  />
)}
```

---

## Phase 5: Help Desk Modal

### 5.1 Create HelpDeskModal Component
**File**: `frontend/src/components/help/HelpDeskModal.tsx`

A compact chat modal for platform help:

```tsx
interface HelpDeskModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function HelpDeskModal({ isOpen, onClose }: HelpDeskModalProps) {
  const [messages, setMessages] = useState<Array<{role: string, content: string}>>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await chatApi.sendHelpMessage({ message: input })
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.content }])
    } catch (err) {
      toast.error('Failed to get help')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Help & Support</DialogTitle>
        </DialogHeader>

        <div className="h-80 overflow-y-auto border rounded p-3 bg-gray-50">
          {messages.length === 0 && (
            <p className="text-gray-500 text-sm">
              Ask me anything about using BC Legal Tech!
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`mb-2 ${msg.role === 'user' ? 'text-right' : ''}`}>
              <span className={`inline-block rounded px-3 py-1 text-sm ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border'
              }`}>
                {msg.content}
              </span>
            </div>
          ))}
        </div>

        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="How can I help?"
            className="flex-1 rounded border px-3 py-2 text-sm"
          />
          <Button onClick={handleSend} disabled={isLoading}>
            {isLoading ? '...' : 'Send'}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
```

### 5.2 Add Help Endpoint
**File**: `backend/app/api/v1/endpoints/chat.py`

```python
@router.post("/help")
async def send_help_message(
    request: HelpRequest,
    current_user: User = Depends(get_current_user)
):
    """Platform help chat - answers questions about using BC Legal Tech"""
    # Simple Claude call with platform help system prompt
    anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

    response = await anthropic.messages.create(
        model="claude-3-haiku-20240307",  # Use cheaper model for help
        max_tokens=500,
        system="""You are a helpful assistant for BC Legal Tech, a legal document
management platform. Answer questions about:
- Uploading and managing documents
- Creating and managing matters
- Using the AI chat feature
- Tracking billable hours
- Viewing document timelines
- User settings and permissions

Keep answers concise and practical. If asked about legal questions (not platform usage),
redirect them to use the main Chat feature with a matter selected.""",
        messages=[{"role": "user", "content": request.message}]
    )

    return {"content": response.content[0].text}
```

### 5.3 Add Help Button to Header
**File**: `frontend/src/components/layout/DashboardLayout.tsx`

Add help icon button that opens the modal:

```tsx
import { HelpCircle } from 'lucide-react'
import HelpDeskModal from '@/components/help/HelpDeskModal'

// In component:
const [helpOpen, setHelpOpen] = useState(false)

// In header, before user menu:
<Button variant="ghost" size="sm" onClick={() => setHelpOpen(true)}>
  <HelpCircle className="h-5 w-5" />
</Button>

<HelpDeskModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
```

---

## Summary: Files to Modify/Create

### Backend
| File | Action |
|------|--------|
| `app/services/chat_service.py` | Modify - Add discovery mode, matter detection |
| `app/api/v1/endpoints/chat.py` | Modify - Add link-matter and help endpoints |
| `app/schemas/chat.py` | Modify - Add MatterSuggestion, HelpRequest schemas |

### Frontend
| File | Action |
|------|--------|
| `src/components/chat/MatterSelectorCompact.tsx` | Modify - Update labels |
| `src/components/chat/MatterSuggestionBanner.tsx` | Create - New component |
| `src/components/help/HelpDeskModal.tsx` | Create - New component |
| `src/components/layout/DashboardLayout.tsx` | Modify - Add help button |
| `src/pages/ChatPage.tsx` | Modify - Handle matter suggestions |
| `src/types/chat.ts` | Modify - Add new types |
| `src/lib/api.ts` | Modify - Add new API methods |

---

## Implementation Order

1. **Phase 1** - Remove "All Matters" (Quick win, immediate UX improvement)
2. **Phase 2** - Backend Discovery Mode (Foundation for new behavior)
3. **Phase 3** - Matter Detection (Core new feature)
4. **Phase 4** - Frontend Suggestion UI (Makes matter detection usable)
5. **Phase 5** - Help Desk Modal (Can be done in parallel with 3-4)

Estimated scope: ~500-700 lines of new/modified code across 10 files.
