# Sentry Error Tracking Setup

This guide will help you set up Sentry for error tracking in both the backend and frontend.

## Step 1: Create a Sentry Account

1. Go to https://sentry.io/signup/
2. Sign up for a free account (5,000 errors/month)
3. Create a new organization (e.g., "BC Legal Tech")

## Step 2: Create Projects

You'll need **two separate projects** - one for backend, one for frontend.

### Backend Project (Python/FastAPI)

1. Click "Create Project"
2. Select platform: **Python**
3. Set alert frequency: **Alert me on every new issue**
4. Name your project: **bc-legal-backend**
5. Click "Create Project"
6. Copy the **DSN** (looks like: `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx`)

### Frontend Project (React)

1. Click "Create Project" again
2. Select platform: **React**
3. Set alert frequency: **Alert me on every new issue**
4. Name your project: **bc-legal-frontend**
5. Click "Create Project"
6. Copy the **DSN** (different from backend DSN)

## Step 3: Configure Backend Environment Variables

Add these to your `.env` file in the `backend/` directory:

```env
# Sentry Error Tracking
SENTRY_DSN=https://your-backend-dsn-here@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Note:** For production, change `SENTRY_ENVIRONMENT=production`

## Step 4: Configure Frontend Environment Variables

Create or update `.env` file in the `frontend/` directory:

```env
# Sentry Error Tracking
VITE_SENTRY_DSN=https://your-frontend-dsn-here@xxxxx.ingest.sentry.io/xxxxx
VITE_SENTRY_ENVIRONMENT=development
```

**Note:** For production builds, create `.env.production`:

```env
VITE_SENTRY_DSN=https://your-frontend-dsn-here@xxxxx.ingest.sentry.io/xxxxx
VITE_SENTRY_ENVIRONMENT=production
```

## Step 5: Test the Integration

### Test Backend Error Tracking

1. Start your backend: `cd backend && uvicorn app.main:app --reload`
2. Trigger a test error by visiting: `http://localhost:8000/api/v1/sentry-test`
   (You can create this endpoint temporarily or trigger an actual error)
3. Or use Python console:
   ```python
   import sentry_sdk
   sentry_sdk.capture_message("Test message from backend")
   ```
4. Check Sentry dashboard - you should see the error appear within seconds

### Test Frontend Error Tracking

1. Start your frontend: `cd frontend && npm run dev`
2. Open browser console and run:
   ```javascript
   throw new Error("Test error from frontend");
   ```
3. Check Sentry dashboard - error should appear in the React project

**IMPORTANT:** Sentry only sends errors in production builds for frontend!
- Development mode: Errors logged to console only
- Production mode: Errors sent to Sentry

To test in production mode:
```bash
cd frontend
npm run build
npm run preview
```

## Step 6: Understanding What Gets Tracked

### Backend Tracking
- ✅ All unhandled exceptions
- ✅ FastAPI route errors
- ✅ Database errors
- ✅ Celery task failures
- ✅ Custom errors using `sentry_sdk.capture_exception()`
- ❌ Health check endpoints (filtered out)

### Frontend Tracking
- ✅ JavaScript errors
- ✅ React component errors (via ErrorBoundary)
- ✅ Network request failures (fetch/axios)
- ✅ Promise rejections
- ❌ Localhost errors (filtered out)
- ❌ Development mode errors (filtered out)

## Step 7: Privacy Configuration

We've configured Sentry to protect sensitive legal data:

**Frontend:**
- `maskAllText: true` - All text is masked in session replays
- `blockAllMedia: true` - No images/videos captured
- No PII (personally identifiable information) sent

**Backend:**
- `send_default_pii: false` - No PII sent automatically
- You can manually add user context for debugging (without PII)

## Step 8: Cost Management

### Free Tier Limits
- **5,000 errors/month** per project
- **10,000 errors/month** total if you have 2 projects
- **Unlimited team members**

### What Counts as an Error?
- Each unique error = 1 event
- Same error repeated 100 times = 100 events (use grouping to reduce)
- Performance transactions also count (we sample 10% to save quota)

### Tips to Stay Under Quota
1. ✅ **Filter health checks** - Already configured
2. ✅ **Sample transactions** - Set to 10% (can lower to 5%)
3. ✅ **Group similar errors** - Sentry does this automatically
4. ✅ **Fix bugs quickly** - Fewer errors = lower costs
5. ⚠️ **Monitor usage** - Check Sentry dashboard weekly

## Step 9: Alert Configuration (Optional)

1. Go to **Settings → Alerts**
2. Set up alerts for:
   - New error types detected
   - Error spike (>50% increase)
   - Specific errors (e.g., payment failures)
3. Connect to Slack or email

## Step 10: Production Deployment Checklist

Before deploying to production:

**Backend:**
- [ ] Add `SENTRY_DSN` to production environment variables
- [ ] Set `SENTRY_ENVIRONMENT=production`
- [ ] Test error tracking in staging first
- [ ] Set up alerts for critical errors

**Frontend:**
- [ ] Add `VITE_SENTRY_DSN` to production build variables
- [ ] Set `VITE_SENTRY_ENVIRONMENT=production`
- [ ] Build and test: `npm run build && npm run preview`
- [ ] Verify errors are being tracked

## Troubleshooting

### Errors Not Appearing in Sentry?

**Backend:**
1. Check `SENTRY_DSN` is set: `echo $SENTRY_DSN`
2. Check Sentry initialization log: Should see "Sentry initialized for environment: development"
3. Verify DSN is correct (copy from Sentry dashboard)
4. Check internet connection (Sentry is cloud-hosted)

**Frontend:**
1. Check browser console for Sentry errors
2. Verify you're in production build: `npm run build && npm run preview`
3. Check Network tab - should see requests to `sentry.io`
4. Verify `VITE_SENTRY_DSN` is set correctly

### Getting Too Many Errors?

1. Check if it's a single error repeating (group by issue)
2. Filter out known non-critical errors
3. Lower sample rates:
   - Backend: `SENTRY_TRACES_SAMPLE_RATE=0.05` (5%)
   - Frontend: `tracesSampleRate: 0.05` in main.tsx

### Privacy Concerns?

Review what data is being sent:
1. Go to Sentry → Issues → Click an error
2. Check "Additional Data" section
3. Verify no sensitive data (document content, passwords)
4. If needed, add custom `before_send` filters

## Support

- Sentry Docs: https://docs.sentry.io/
- Sentry Support: help@sentry.io
- Free tier support: Community forum

---

**Note:** Sentry integration is optional for development but **highly recommended** for production. It dramatically reduces debugging time and improves user experience by catching errors before users report them.
