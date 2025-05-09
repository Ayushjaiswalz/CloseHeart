from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Read the database URL from .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Safety check
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file!")

# Print the connection string for debugging
print(f"Connecting to database: {DATABASE_URL}")

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,       # default is 5
    max_overflow=20,    # allow 20 extra temporary connections
    pool_timeout=30  # wait 30s before raising error
)
# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialize database tables
def init_db():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done.")

# Run only if file is executed directly
if __name__ == '__main__':
    init_db()
