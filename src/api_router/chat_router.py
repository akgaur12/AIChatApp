import os, logging
from fastapi import APIRouter, Depends, HTTPException


logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chat")
def chat():
    return {"message": "Hello World"}





    