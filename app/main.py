"""Main FastAPI application for Nutrition Facts Vision API."""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth
from app.api.v1 import health_profile
from app.api.v1 import scan
from app.api.v1 import chat

load_dotenv()

app = FastAPI(
    title="Nutrition Facts Vision API",
    description="API for nutrition facts recognition and user management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(
    health_profile.router, prefix="/api/v1/health-profile", tags=["Health Profile"]
)
app.include_router(scan.router, prefix="/api/v1/scans", tags=["Scans"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Nutrition Facts Vision API"}
