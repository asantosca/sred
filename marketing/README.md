# BC Legal Tech - Marketing Website

Next.js 14 marketing website for BC Legal Tech platform.

## Tech Stack

- **Next.js 14** (App Router, Static Export)
- **TypeScript**
- **TailwindCSS**
- **React Hook Form** (for forms)

## Development

```bash
# Install dependencies
npm install

# Run development server (port 3001 to avoid conflict with main app)
npm run dev

# Build for production
npm run build

# View production build locally
npm start
```

## Deployment

This site is configured for static export and deploys to **AWS Amplify**.

### Amplify Configuration

The site automatically deploys from the `/marketing` folder when changes are pushed to GitHub.

See `amplify.yml` for build configuration.

## Folder Structure

```
marketing/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── page.tsx      # Landing page
│   │   ├── features/     # Features page
│   │   ├── about/        # About page
│   │   ├── contact/      # Contact/waitlist page
│   │   ├── privacy/      # Privacy policy
│   │   ├── terms/        # Terms of service
│   │   └── cookies/      # Cookie policy
│   ├── components/       # Reusable React components
│   └── lib/              # Utilities and helpers
├── public/               # Static assets (images, etc.)
└── package.json
```

## Environment Variables

Create `.env.local` for local development:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Pages

- `/` - Landing page with hero, features, waitlist
- `/features` - Detailed product features
- `/about` - Company information
- `/contact` - Contact form and waitlist signup
- `/privacy` - Privacy policy
- `/terms` - Terms of service
- `/cookies` - Cookie policy
