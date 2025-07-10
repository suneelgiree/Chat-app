import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:suneel@localhost/chatapp")
SECRET_KEY = os.getenv("SECRET_KEY", "3nnDAFEa9EeDbVLhZcsWjPY5Fct7jVr7Q9Rj7Hsc5Yc")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))