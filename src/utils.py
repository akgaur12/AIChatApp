from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import yaml


# Load configuration from YAML file function
def load_config():
    with open("src/config/config.yml", "r") as f:
        config = yaml.safe_load(f)
    return config


# Load configuration
cfg = load_config()
SECRET_KEY = cfg["Security"]["SECRET_KEY"]
ALGORITHM = cfg["Security"]["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = cfg["Security"]["ACCESS_TOKEN_EXPIRE_MINUTES"]

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Password verification
def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

# JWT token creation
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    # Set expiration time
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    # Update token data
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
    })
    
    # Encode and return token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
