import os, logging
from fastapi import APIRouter, HTTPException, status, Depends

from src.database import users_collection
from src.schemas import UserCreate, UserLogin, Token, ResetPasswordRequest
from src.utils import hash_password, verify_password, create_access_token
from src.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ---------------- SIGNUP ----------------
@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate):
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = {
        "email": user.email,
        "hashed_password": hash_password(user.password)
    }

    await users_collection.insert_one(new_user)
    return {"message": "User created successfully"}


# ---------------- LOGIN ----------------
@router.post("/login", response_model=Token)
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": db_user["email"]})

    return {"access_token": access_token}


# ---------------- LOGOUT ----------------
@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    return {"message": "Logged out successfully"}


# ---------------- RESET PASSWORD ----------------
@router.put("/reset-password")
async def reset_password(data: ResetPasswordRequest, current_user=Depends(get_current_user)):
    if not verify_password(data.old_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": hash_password(data.new_password)}}
    )

    return {"message": "Password updated successfully"}


# ---------------- DELETE USER ----------------
@router.delete("/delete")
async def delete_user(current_user=Depends(get_current_user)):
    print(current_user)
    await users_collection.delete_one({"_id": current_user["_id"]})
    return {"message": "User deleted successfully"}



    