import os
from datetime import datetime, timedelta
from typing import Optional

# This module provides basic utilities for legacy auth if needed.
# Note: Main auth is now handled via Supabase on the frontend.

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Mock implementation of token creation for compatibility
    return "mock_token_" + str(datetime.now().timestamp())

def verify_token(token: str):
    # Mock token verification
    return token.startswith("mock_token_") or token.startswith("eyJ") # Support Supabase JWTs too

def get_current_user(token: str):
    # Mock user retrieval
    return {"email": "user@example.com", "role": "compliance_officer"}
