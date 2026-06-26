#!/usr/bin/env python3
"""Test script to verify LLM configuration."""
import asyncio
from app.core.config import settings
from app.services import triage_service

async def test_llm():
    print("=== LLM Configuration Test ===")
    print(f"GROQ_API_KEY set: {bool(settings.groq_api_key)}")
    print(f"GEMINI_API_KEY set: {bool(settings.gemini_api_key)}")
    print(f"Primary provider: {settings.llm_primary_provider}")
    print(f"GROQ_MODEL: {settings.groq_model}")
    print(f"GEMINI_MODEL: {settings.gemini_model}")
    print()
    
    print("=== Testing Triage Service ===")
    symptoms = "eye pain and headache"
    print(f"Analyzing: '{symptoms}'")
    
    try:
        result = await triage_service.analyze(symptoms)
        if result:
            print(f"✅ SUCCESS!")
            print(f"  Source: {result.source}")
            print(f"  Urgency: {result.urgency}")
            print(f"  Department: {result.department}")
            print(f"  Confidence: {result.confidence}")
            print(f"  Reasoning: {result.reasoning}")
        else:
            print("❌ FAILED: No result returned")
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_llm())