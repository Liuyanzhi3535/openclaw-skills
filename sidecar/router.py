from fastapi import FastAPI
from skills.calendar_gcal import router as calendar_router

app = FastAPI()

app.include_router(calendar_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
