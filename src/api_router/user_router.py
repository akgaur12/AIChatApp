import logging
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.database import conversations_collection, messages_collection, users_collection
from src.deps import RoleChecker, get_current_user
from src.schemas import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ResetPasswordWithOTP,
    Token,
    UpdateUserNameRequest,
    UserCreate,
    UserLogin,
)
from src.utils import (
    create_access_token,
    generate_otp,
    hash_password,
    send_otp_email,
    verify_password,
)

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
        "hashed_password": hash_password(user.password),
        "role": ["ROLE_USER", "ROLE_ADMIN"] if "ROLE_ADMIN" in user.role else user.role
    }

    await users_collection.insert_one(new_user)
    return {"message": "User created successfully"}


# ---------------- LOGIN (SWAGGER/OAUTH2) ----------------
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


# ---------------- LOGIN-JSON (FRONTEND) ----------------
@router.post("/login-json", response_model=Token)
async def login_json(user: UserLogin):
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


# ---------------- UPDATE USER NAME ----------------
@router.put("/update-user-name")
async def update_user_name(data: UpdateUserNameRequest, current_user=Depends(get_current_user)):
    
    await users_collection.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"name": data.new_name}}
    )

    return {"message": "User name updated successfully"}


# ---------------- DELETE ACCOUNT ----------------
@router.delete("/delete-user")
async def delete_user(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    
    # 1. Find all conversations for this user to get their IDs
    cursor = conversations_collection.find({"user_id": user_id}, {"_id": 1})
    conversation_ids = [doc["_id"] async for doc in cursor] # extraction requires async iteration
    
    # 2. Convert ObjectIds to strings if stored as strings in messages (based on chat_router), 
    #    but chat_router uses string conversation_id in messages. 
    #    Let's check chat_router again: 
    #    conversation_id = str(result.inserted_id) -> stored as string in messages "chat_id"
    chat_ids_str = [str(cid) for cid in conversation_ids]

    if chat_ids_str:
        # 3. Delete all messages for these conversations
        await messages_collection.delete_many({"chat_id": {"$in": chat_ids_str}})

    # 4. Delete all conversations for this user
    await conversations_collection.delete_many({"user_id": user_id})

    # 5. Delete the user
    await users_collection.delete_one({"_id": current_user["_id"]})
    
    return {"message": "User and all associated data deleted successfully"}


# ---------------- FORGOT PASSWORD ----------------
@router.post("/forget-password")
async def forget_password(request: ForgotPasswordRequest):
    user = await users_collection.find_one({"email": request.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    otp = generate_otp()
    otp_expiry = datetime.now(UTC) + timedelta(minutes=5)

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

    if datetime.now(UTC) > user["otp_expiry"]:
        raise HTTPException(status_code=400, detail="OTP expired. Please request a new one.")

    await users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {"hashed_password": hash_password(request.new_password)},
            "$unset": {"otp": "", "otp_expiry": ""}
        }
    )

    return {"message": "Password reset successfully"}


# ---------------- ADMIN ONLY ----------------
@router.get("/admin-only")
async def admin_only_route(admin_user=Depends(RoleChecker(["ROLE_ADMIN"]))):
    return {"message": f"Hello Admin {admin_user['name']}, you have access!"}




    