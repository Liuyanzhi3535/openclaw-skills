from fastapi import FastAPI

from skills.calendar_gcal import router as calendar_router
from skills.twfood_fetch import router as twfood_router

app = FastAPI()

app.include_router(calendar_router)
app.include_router(twfood_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
