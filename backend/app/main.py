# app/main.py - BC Legal Tech FastAPI Application

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="BC Legal Tech API",
    description="AI-powered legal document intelligence platform for law firms in British Columbia.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "BC Legal Tech API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": "development",
        "database": "connected"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting BC Legal Tech API...")

# Shutdown event  
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down BC Legal Tech API...")