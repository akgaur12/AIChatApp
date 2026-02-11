# Standard library
import logging
import os
import random
import smtplib
import string
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

# Third-party
import bcrypt
import yaml
from dotenv import load_dotenv
from jose import jwt
from langchain_core.messages import HumanMessage, SystemMessage

# Logger
logger = logging.getLogger(__name__)


# Load configuration from YAML file function
def load_config(filename="config.yml"):
    with open("src/config/" + filename, "r") as f:
        config = yaml.safe_load(f)
    return config


# Load environment variables and configuration and set IST timezone
load_dotenv()
cfg = load_config()

# Security Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or cfg["Security"]["JWT_SECRET_KEY"]
ALGORITHM = cfg["Security"]["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = cfg["Security"]["ACCESS_TOKEN_EXPIRE_MINUTES"]

# Email Configuration
SMTP_SERVER = cfg["Email"]["SMTP_SERVER"]
SMTP_PORT = cfg["Email"]["SMTP_PORT"]
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or cfg["Email"]["SENDER_EMAIL"]
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") or cfg["Email"]["SENDER_PASSWORD"]

# bcrypt salt generation
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Password hashing
def hash_password(password: str) -> str:
    # bcrypt requires bytes
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# Password verification
def verify_password(password: str, hashed_password: str) -> bool:
    # bcrypt requires bytes
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

# JWT token creation
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    # Set expiration time
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    # Update token data
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
    })
    
    # Encode and return token
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)


# Generate OTP
def generate_otp(length=6) -> str:
    return ''.join(random.choices(string.digits, k=length))

# Send OTP Email
def send_otp_email(to_email: str, otp: str) -> bool:
    try:
        msg = EmailMessage()
        msg['From'] = f"AIChatApp Support <{SENDER_EMAIL}>"
        msg['To'] = to_email
        msg['Subject'] = "AIChatApp Password Reset OTP"

        msg.set_content(f"Your OTP for password reset is: {otp}. It is valid for 5 minutes.")

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


# Generate Chat Title
async def generate_chat_title(user_query: str, llm_model, parse_response) -> str:
    """
    Generates a short, descriptive title for a conversation based on the initial query.
    Uses dependency injection for llm_model and parse_response to avoid circular imports.
    """
    try:
        # Improved prompt for more concise and relevant titles
        prompt = (
            "You are a helpful assistant. Generate a short, 3-5 word title for a conversation "
            "that starts with the following user query. The title should be descriptive but concise. "
            "Do not use quotes, periods, or prefixes like 'Title:'."
        )
        
        response = await llm_model.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content=user_query)
            ]
        )
      
        # Parse and clean the title
        parsed = parse_response(response)
        
        # Safely extract content regardless of whether it's an AIMessage or raw string
        title = getattr(parsed, "content", str(parsed)).strip()
        
        # Remove surrounding quotes if the LLM included them
        if title.startswith('"') and title.endswith('"') or title.startswith("'") and title.endswith("'"):
            title = title[1:-1]
            
        return title or user_query[:30]
    except Exception as e:
        logger.error(f"Error generating title: {e}", exc_info=True)
        # Fallback to a truncated version of the query
        return user_query[:30]