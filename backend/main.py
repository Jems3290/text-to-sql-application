from fastapi import FastAPI
from backend.api.chat_routes import router as chat_router
from backend.api.database_routes import router as database_router

app = FastAPI(
    title="Conversational Text-to-SQL API",
    description="Backend API for interacting with uploaded SQLite databases using natural language.",
    version="1.0.0"
)

app.include_router(database_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "Conversational Text-to-SQL API is running."
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}