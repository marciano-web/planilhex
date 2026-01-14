"""Creates initial admin user if not exists."""
from sqlalchemy.orm import Session
from .db import SessionLocal, engine
from .models import Base, User
from .config import settings
from .security import hash_password

def main():
    # Ensure metadata exists (alembic will manage real schema; this helps first run)
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == settings.admin_email).first()
        if not user:
            db.add(User(
                email=settings.admin_email,
                password_hash=hash_password(settings.admin_password),
                role="admin",
            ))
            db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    main()
