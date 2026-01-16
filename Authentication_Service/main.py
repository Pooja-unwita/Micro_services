import uvicorn
from fastapi import FastAPI
from routers import auth

app = FastAPI(
    title="Authentication Service",
    version="1.0.0"
)
app.include_router(auth.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)