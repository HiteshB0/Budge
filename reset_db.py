from app.db.session import engine
from app.models.allmodels import Base

print("🗑️  Dropping all tables...")
Base.metadata.drop_all(bind=engine)

print("✨ Creating fresh tables...")
Base.metadata.create_all(bind=engine)

print("✅ Database reset complete!")