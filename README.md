# BC Legal Tech

AI-powered legal document intelligence platform for Canadian law firms.

## Quick Start

1. **Start local services:**

   ```bash
   docker-compose up -d
   ```

2. **Setup backend:**

   ```bash
   cd backend
   poetry install
   poetry run uvicorn app.main:app --reload
   ```

3. **Setup frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Project Structure

```
bc-legal-tech/
├── backend/     # FastAPI backend
├── frontend/    # React frontend
├── infrastructure/  # Terraform configs
├── docker-compose.yml   # Local development services
└── setup-database.sql   # Database schema
```

## Development Workflow

1. Backend runs on http://localhost:8000
2. Frontend runs on http://localhost:5173
3. PostgreSQL with PGvector on localhost:5432
4. Redis cache on localhost:6379
5. LocalStack S3 on localhost:4566

## Next Steps

1. Review and customize environment variables
2. Set up authentication with JWT
3. Implement document upload to S3
4. Build RAG pipeline with PGvector
5. Create React components with Tailwind

## Documentation

- [API Documentation](backend/README.md)
- [Frontend Guide](frontend/README.md)
- [Infrastructure Setup](infrastructure/README.md)
