from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.calculator import router as calc_router
from .api.history import router as history_router
from .api.vision import router as vision_router
from .database.database import engine
from .database import models  # noqa: F401 - needed for table creation

# Ensure tables exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MayoMandi API",
    description="Mandi-to-mayo finder (scientifically unnecessary)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(calc_router)
app.include_router(history_router)
app.include_router(vision_router)



@app.get("/health")
def health():
    return {"status": "MayoMandi operational"}
