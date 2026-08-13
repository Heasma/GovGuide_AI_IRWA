import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database.connection import engine
from app.models.user import User
from app.security.password_hasher import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_demo_user():
    async with AsyncSession(engine) as session:
        # Check if the demo user already exists
        result = await session.execute(select(User).where(User.email == "demo@gmail.com"))
        user = result.scalar_one_or_none()
        
        if user:
            logger.info("Demo user 'demo@gmail.com' already exists in the database. No changes made.")
            return
        
        logger.info("Creating demo user 'demo@gmail.com'...")
        
        # Use existing utility to hash the password safely
        password_hash = hash_password("password")
        
        demo_user = User(
            email="demo@gmail.com",
            password_hash=password_hash,
            is_active=True,
            role="public"
        )
        
        session.add(demo_user)
        await session.commit()
        
        logger.info("Demo user 'demo@gmail.com' successfully created!")

if __name__ == "__main__":
    logger.info("--- DEMO ACCOUNT SEED SCRIPT ---")
    logger.info("This is for DEVELOPMENT / ACADEMIC DEMONSTRATION ONLY.")
    
    # Run the async script
    asyncio.run(seed_demo_user())
