from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserLogin, UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201,
             summary="Register a new user account")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user (Admin or Inventory Manager)."""
    return await AuthService(db).register(data)


@router.post("/login", response_model=TokenResponse,
             summary="Login and receive a JWT token")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate with email/password and receive access token."""
    try:
        return await AuthService(db).login(data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me", response_model=UserResponse,
            summary="Get currently authenticated user")
async def me(current_user: User = Depends(get_current_user)):
    """Returns the currently authenticated user's profile."""
    return current_user
