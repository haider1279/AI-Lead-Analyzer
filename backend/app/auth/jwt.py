import os
import json
import logging
from fastapi import Depends, HTTPException, status, Header
from typing import Optional, Dict, Any
from ..db.database import db
from ..utils.config import settings

logger = logging.getLogger("auth")

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    # Extract Bearer token from Authorization header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]

    if not db.supabase:
        logger.error("[CRITICAL AUTH] Supabase client is not configured. Rejecting request.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is currently unavailable. Supabase is not configured.",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify token with Supabase Auth
    user_id = None
    email = None
    user_meta = {}

    try:
        user_resp = db.supabase.auth.get_user(token)
        if user_resp and user_resp.user:
            sb_user = user_resp.user
            user_id = str(sb_user.id)
            email = sb_user.email
            user_meta = sb_user.user_metadata or {}
    except Exception as e:
        logger.warning(f"[Auth] Supabase auth.get_user failed: {e}")

    # Fallback to direct JWT decode if get_user was unreachable and JWT secret is configured
    if not user_id and settings.SUPABASE_JWT_SECRET:
        try:
            import jwt
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            user_id = payload.get("sub")
            email = payload.get("email")
            user_meta = payload.get("user_metadata") or {}
        except Exception as jwt_err:
            logger.warning(f"[Auth] Direct JWT decode failed: {jwt_err}")

    if user_id:
        profile = await db.get_profile(user_id)
        if profile:
            # Authoritative role from public.profiles
            return profile
        
        # Profile record not yet created; default safely to employee
        # NEVER trust user_metadata for role escalation
        return {
            "id": user_id,
            "email": email or "",
            "name": user_meta.get("name", (email or "User").split("@")[0]),
            "role": "employee"
        }

    # Supabase token verification failed — reject
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

