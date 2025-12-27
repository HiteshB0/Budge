from app.db.session import SessionLocal
from app.services.rag_service import rag_service

def initialize():
    db = SessionLocal()
    try:
        print("🔄 Initializing concept embeddings...")
        rag_service.initialize_embeddings(db)
        print("✅ Embeddings initialized successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize()