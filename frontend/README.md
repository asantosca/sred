# PwC SR&ED Intelligence Platform - Frontend

AI-Powered SR&ED Document Intelligence Platform

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router DOM v6
- **State Management**: Zustand (with persist middleware)
- **API Client**: Axios with interceptors
- **Data Fetching**: TanStack React Query
- **Form Validation**: React Hook Form + Zod
- **Styling**: TailwindCSS
- **Icons**: Lucide React
- **UI Components**: Custom components with Headless UI

## Features Implemented

### Authentication & Authorization
- [x] User Login with JWT
- [x] Company Registration with admin user
- [x] Email Confirmation Flow
- [x] Password Reset Flow
- [x] Protected Routes
- [x] Auto Token Refresh
- [x] Logout with Token Revocation

### SR&ED Features
- [x] Claim Management (create, view, edit)
- [x] Document Upload with SR&ED metadata
- [x] AI Chat with RAG context
- [x] Project Timeline view
- [x] Consulting Hours tracking
- [ ] Eligibility Report generation
- [ ] T661 Form drafting

### UI Components
- [x] Button (variants: primary, secondary, outline, ghost, danger)
- [x] Input (with label, error, helper text)
- [x] Card (with header, title, description, content, footer)
- [x] Alert (variants: info, success, warning, error)
- [x] Dashboard Layout (with sidebar and navigation)
- [x] Protected Route Wrapper

### Pages
- [x] Login Page
- [x] Registration Page
- [x] Dashboard Page
- [x] Claims Page (list claims)
- [x] Claim Detail Page
- [x] Create/Edit Claim Pages
- [x] Documents Page
- [x] Chat Page
- [x] Timeline Page
- [x] Consulting Hours Page
- [x] Profile Page

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

This starts the dev server at `http://localhost:3000`

The Vite config includes a proxy for API calls:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000/api/v1` (proxied from `/api`)

### Build for Production

```bash
npm run build
```

Outputs to `dist/` directory.

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable components
│   │   ├── layout/      # Layout components
│   │   ├── chat/        # Chat components
│   │   ├── documents/   # Document components
│   │   ├── eligibility/ # Eligibility report components
│   │   ├── t661/        # T661 form components
│   │   └── ui/          # UI components
│   ├── lib/             # Utilities and libraries
│   │   └── api.ts       # Axios client with interceptors
│   ├── pages/           # Page components
│   │   ├── ClaimsPage.tsx
│   │   ├── ClaimDetailPage.tsx
│   │   ├── CreateClaimPage.tsx
│   │   ├── ChatPage.tsx
│   │   ├── DocumentsPage.tsx
│   │   ├── TimelinePage.tsx
│   │   └── ...
│   ├── store/           # State management
│   │   └── authStore.ts # Zustand auth store
│   ├── types/           # TypeScript types
│   │   ├── auth.ts
│   │   ├── claims.ts
│   │   └── documents.ts
│   ├── utils/           # Utility functions
│   ├── App.tsx          # Main app with routing
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles + Tailwind
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

## State Management

### Auth Store (Zustand)

The auth store manages:
- User data
- Company data
- Access & refresh tokens
- Authentication state
- Login/logout actions

Data is persisted to localStorage via the `persist` middleware.

## API Client

The Axios client (`src/lib/api.ts`) includes:

1. **Request Interceptor**: Automatically adds JWT token to requests
2. **Response Interceptor**: Handles 401 errors and auto-refreshes tokens
3. **Auth API**: Authentication endpoints
4. **Claims API**: Claim management endpoints
5. **Documents API**: Document upload and management
6. **Chat API**: AI chat endpoints
7. **Eligibility API**: Eligibility report generation
8. **T661 API**: T661 form drafting

## Forms & Validation

Forms use:
- **React Hook Form** for form state
- **Zod** for schema validation
- Custom Input components with error display

## Styling

TailwindCSS is used for all styling with:
- Custom color palette (primary colors)
- Responsive design
- PwC-inspired branding

## Security Features

1. **Token Management**:
   - Access tokens (15 min expiry)
   - Refresh tokens (7 day expiry)
   - Auto-refresh on 401

2. **Protected Routes**:
   - Redirect to login if not authenticated
   - Save attempted location for post-login redirect

## SR&ED-Specific Types

```typescript
// types/claims.ts
export const PROJECT_TYPES = [
  'Software Development',
  'Manufacturing Process',
  'Product Design',
  'Chemical/Biological',
  'Engineering',
  'Other'
] as const;

export const CLAIM_STATUSES = [
  'draft',
  'in_progress',
  'under_review',
  'submitted',
  'approved',
  'rejected'
] as const;

export interface Claim {
  id: string;
  company_id: string;
  claim_number: string;
  company_name: string;
  project_type: string;
  claim_status: string;
  fiscal_year_end: string;
  naics_code?: string;
  // ...
}
```

## Notes

- Email changes require admin/support (security requirement)
- All auth flows match backend implementation
- Token refresh is automatic and transparent
