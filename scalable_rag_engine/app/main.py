from fastapi import FastAPI

app = FastAPI(title="Scalable RAG Engine", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Welcome to the Scalable RAG Engine! Visit /docs for the API UI."};
