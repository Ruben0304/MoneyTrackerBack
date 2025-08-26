from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from models import UserCreate, UserLogin, TokenResponse, RefreshTokenRequest, UserUpdate
from database import users_collection
from auth import AuthService, get_current_active_user, user_helper
from bson import ObjectId

router = APIRouter(prefix="/auth", tags=["authentication"])

def get_ai_limits_by_role(role: str) -> dict:
    """Get AI request limits based on user role"""
    limits = {
        "basic": {"limit": 10, "name": "Basic"},
        "pro": {"limit": 100, "name": "Pro"},
        "max": {"limit": -1, "name": "Max"}  # -1 means unlimited
    }
    return limits.get(role, limits["basic"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    # Check if user already exists
    existing_user = users_collection.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get AI limits based on role
    ai_limits = get_ai_limits_by_role(user_data.role)
    
    # Create user document
    user_dict = {
        "name": user_data.name,
        "email": user_data.email,
        "password_hash": AuthService.hash_password(user_data.password),
        "role": user_data.role,
        "is_active": True,
        "ai_requests_limit": ai_limits["limit"],
        "ai_requests_used": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    # Insert user
    result = users_collection.insert_one(user_dict)
    new_user = users_collection.find_one({"_id": result.inserted_id})
    
    # Create tokens
    user_id = str(new_user["_id"])
    access_token = AuthService.create_access_token(data={"sub": user_id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=user_helper(new_user)
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    """Login user"""
    user = AuthService.authenticate_user(user_credentials.email, user_credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create tokens
    user_id = str(user["_id"])
    access_token = AuthService.create_access_token(data={"sub": user_id})
    refresh_token = AuthService.create_refresh_token(data={"sub": user_id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=user_helper(user)
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_data: RefreshTokenRequest):
    """Refresh access token"""
    try:
        # Verify refresh token
        payload = AuthService.verify_token(refresh_data.refresh_token, token_type="refresh")
        user_id = payload.get("sub")
        
        # Get user
        user = AuthService.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create new tokens
        access_token = AuthService.create_access_token(data={"sub": user_id})
        new_refresh_token = AuthService.create_refresh_token(data={"sub": user_id})
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800,
            user=user_helper(user)
        )
        
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_active_user)):
    """Get current user information"""
    return user_helper(current_user)

@router.put("/me")
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_active_user)
):
    """Update current user information"""
    update_data = user_update.dict(exclude_unset=True)
    
    # Remove sensitive fields that users shouldn't update directly
    if "role" in update_data:
        del update_data["role"]  # Role changes should be handled separately
    if "is_active" in update_data:
        del update_data["is_active"]  # Only admin can deactivate users
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    # Check if email is being changed and if it's already taken
    if "email" in update_data:
        existing_user = users_collection.find_one({
            "email": update_data["email"],
            "_id": {"$ne": current_user["_id"]}
        })
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Update user
    result = users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_data}
    )
    
    if result.modified_count == 1:
        updated_user = users_collection.find_one({"_id": current_user["_id"]})
        return user_helper(updated_user)
    
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to update user"
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_active_user)):
    """Logout user (client should delete tokens)"""
    return {"message": "Successfully logged out"}

@router.get("/ai-usage")
async def get_ai_usage(current_user: dict = Depends(get_current_active_user)):
    """Get current AI usage for the user"""
    return {
        "role": current_user.get("role", "basic"),
        "requests_limit": current_user.get("ai_requests_limit", 10),
        "requests_used": current_user.get("ai_requests_used", 0),
        "requests_remaining": max(0, current_user.get("ai_requests_limit", 10) - current_user.get("ai_requests_used", 0)) if current_user.get("ai_requests_limit", 10) > 0 else -1
    }

@router.post("/ai-usage/increment")
async def increment_ai_usage(current_user: dict = Depends(get_current_active_user)):
    """Increment AI usage counter"""
    current_used = current_user.get("ai_requests_used", 0)
    limit = current_user.get("ai_requests_limit", 10)
    
    # Check if user has unlimited requests (max role)
    if limit == -1:
        return {"message": "Unlimited requests available"}
    
    # Check if user has reached limit
    if current_used >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="AI request limit reached. Please upgrade your plan."
        )
    
    # Increment usage
    users_collection.update_one(
        {"_id": current_user["_id"]},
        {
            "$inc": {"ai_requests_used": 1},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {
        "requests_used": current_used + 1,
        "requests_limit": limit,
        "requests_remaining": limit - (current_used + 1)
    }