import os, logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from src.database import users_collection
from src.schemas import UserCreate, UserLogin, Token, ResetPasswordRequest, ForgotPasswordRequest, ResetPasswordWithOTP
from src.utils import hash_password, verify_password, create_access_token, generate_otp, send_otp_email
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
        "name": user.name,
        "email": user.email,
        "hashed_password": hash_password(user.password)
    }

    await users_collection.insert_one(new_user)
    return {"message": "User created successfully"}


# ---------------- LOGIN ----------------
# Swagger/OAuth2 login
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Swagger sends username, not email
    email = form_data.username
    password = form_data.password

    db_user = await users_collection.find_one({"email": email})

    if not db_user or not verify_password(password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(data={"sub": db_user["email"], "name": db_user["name"]})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# frontend/JSON login
@router.post("/login-json", response_model=Token)
async def login(user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})

    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token(data={"sub": db_user["email"], "name": db_user["name"]})

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


# ---------------- FORGOT PASSWORD ----------------
@router.post("/forget-password")
async def forget_password(request: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    otp_expiry = datetime.now(timezone.utc) + timedelta(minutes=5)

    await users_collection.update_one(
        {"_id": user["_id"]},
        {"$set": {"otp": otp, "otp_expiry": otp_expiry}}
    )

    if send_otp_email(request.email, otp):
        return {"message": "OTP sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send email")


# ---------------- RESET PASSWORD WITH OTP ----------------
@router.post("/verify-otp-reset-password")
async def verify_otp_reset_password(request: ResetPasswordWithOTP):
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "otp" not in user or "otp_expiry" not in user:
        raise HTTPException(status_code=400, detail="OTP not requested")

    if user["otp"] != request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if datetime.now(timezone.utc) > user["otp_expiry"]:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"hashed_password": hash_password(request.new_password)},
            "$unset": {"otp": "", "otp_expiry": ""}
        }
    )

    return {"message": "Password reset successfully"}



    