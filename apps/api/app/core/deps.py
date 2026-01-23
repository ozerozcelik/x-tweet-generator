"""
Dependency injection utilities.
"""

from typing import Annotated, Generator
from fastapi import Depends, Header, HTTPException, status
from supabase import create_client, Client

from app.core.config import settings


async def get_supabase() -> Generator[Client, None, None]:
    """Get Supabase client instance."""
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
    try:
        yield client
    finally:
        pass


async def verify_authorization(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Verify authorization header and extract user ID.

    This validates the JWT token from Supabase and extracts the user ID.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = authorization.split(" ")[1]

    # Verify token with Supabase
    try:
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )
        user = client.auth.get_user(token)

        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        return user.user.id

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def get_optional_user_id(
    authorization: Annotated[str | None, Header()] = None
) -> str | None:
    """Get user ID from authorization header if present."""
    if not authorization:
        return None

    try:
        return await verify_authorization(authorization)
    except HTTPException:
        return None


# Type aliases for dependencies
SupabaseDep = Annotated[Client, Depends(get_supabase)]
UserDep = Annotated[str, Depends(verify_authorization)]
OptionalUserDep = Annotated[str | None, Depends(get_optional_user_id)]
