# BC Legal Tech - Frontend

AI-Powered Legal Document Intelligence Platform

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
- [x] Password Reset Flow (Request → Verify → Confirm)
- [x] Protected Routes
- [x] Auto Token Refresh
- [x] Logout with Token Revocation

### User Management
- [x] User Profile View
- [x] User Profile Editing (name only, email immutable)
- [x] Avatar Upload (base64 MVP)
- [x] Company Information Display

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
- [x] Forgot Password Page
- [x] Reset Password Page
- [x] Email Confirmation Page
- [x] Dashboard Page
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

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable components
│   │   ├── layout/      # Layout components (DashboardLayout, ProtectedRoute)
│   │   └── ui/          # UI components (Button, Input, Card, Alert)
│   ├── lib/             # Utilities and libraries
│   │   └── api.ts       # Axios client with interceptors
│   ├── pages/           # Page components
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── ForgotPasswordPage.tsx
│   │   ├── ResetPasswordPage.tsx
│   │   ├── ConfirmEmailPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── ProfilePage.tsx
│   ├── store/           # State management
│   │   └── authStore.ts # Zustand auth store
│   ├── types/           # TypeScript types
│   │   └── auth.ts      # Auth-related types
│   ├── utils/           # Utility functions
│   │   └── cn.ts        # TailwindCSS class merger
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
- Token refresh

Data is persisted to localStorage via the `persist` middleware.

## API Client

The Axios client (`src/lib/api.ts`) includes:

1. **Request Interceptor**: Automatically adds JWT token to requests
2. **Response Interceptor**: Handles 401 errors and auto-refreshes tokens
3. **Auth API**: All authentication endpoints
4. **User API**: User management endpoints

## Forms & Validation

Forms use:
- **React Hook Form** for form state
- **Zod** for schema validation
- Custom Input components with error display

Example validation (Registration):
```typescript
const registerSchema = z.object({
  company_name: z.string().min(2),
  admin_email: z.string().email(),
  admin_password: z.string()
    .min(8)
    .regex(/[A-Z]/, 'Must contain uppercase')
    .regex(/[a-z]/, 'Must contain lowercase')
    .regex(/[0-9]/, 'Must contain digit'),
})
```

## Styling

TailwindCSS is used for all styling with:
- Custom color palette (primary colors)
- Responsive design
- Dark mode support (future)
- Custom scrollbar styles

## Security Features

1. **Token Management**:
   - Access tokens (15 min expiry)
   - Refresh tokens (7 day expiry)
   - Auto-refresh on 401

2. **Protected Routes**:
   - Redirect to login if not authenticated
   - Save attempted location for post-login redirect

3. **Email Immutability**:
   - Users cannot change email via self-service
   - Requires admin/support contact

4. **Password Validation**:
   - Min 8 characters
   - Uppercase, lowercase, digit required

## Next Steps (Future Milestones)

- [ ] Document Management (upload, view, organize)
- [ ] AI Chat with Documents
- [ ] User Management (for admins)
- [ ] Team Collaboration
- [ ] Settings & Preferences
- [ ] S3 Avatar Upload (replace base64 MVP)
- [ ] Dark Mode
- [ ] Mobile Responsive Improvements

## Notes

- Avatar upload is MVP implementation (base64 storage)
- Email changes require admin/support (security requirement)
- All auth flows match backend implementation
- Token refresh is automatic and transparent
