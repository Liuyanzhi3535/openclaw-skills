from collections import defaultdict
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/skill/twfood-fetch")

API_URL = "https://data.moa.gov.tw/Service/OpenData/FromM/FarmTransData.aspx"

# 種類代碼
CATEGORY_VEGE = "N04"
CATEGORY_FRUIT = "N05"


def _to_roc(d: date) -> str:
    """轉民國年格式，例：2026-04-02 → 115.04.02"""
    return f"{d.year - 1911}.{d.month:02d}.{d.day:02d}"


async def _fetch_raw(start: date, end: date) -> list[dict]:
    params = {
        "$top": 9999,
        "StartDate": _to_roc(start),
        "EndDate": _to_roc(end),
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(API_URL, params=params)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"農委會 API 請求失敗: {e}")
    return resp.json()


def _aggregate(records: list[dict], category: str) -> list[dict]:
    """同一作物跨市場加總交易量，加權平均價格。"""
    by_crop: dict[str, dict] = defaultdict(lambda: {
        "total_volume": 0.0,
        "weighted_price_sum": 0.0,
        "markets": [],
    })

    for r in records:
        if r["種類代碼"] != category:
            continue
        name = r["作物名稱"]
        vol = r["交易量"] or 0
        price = r["平均價"] or 0
        by_crop[name]["total_volume"] += vol
        by_crop[name]["weighted_price_sum"] += vol * price
        by_crop[name]["markets"].append(r["市場名稱"])

    result = []
    for name, agg in by_crop.items():
        vol = agg["total_volume"]
        avg_price = agg["weighted_price_sum"] / vol if vol > 0 else 0
        result.append({
            "name": name,
            "avg_price_kg": round(avg_price, 1),
            "total_volume_kg": int(vol),
            "market_count": len(set(agg["markets"])),
        })

    result.sort(key=lambda x: x["total_volume_kg"], reverse=True)
    return result


# ---------- endpoint ----------

class FetchRequest(BaseModel):
    top_n: int = 10
    include_fruit: bool = False
    days: int = 1  # 查最近幾天（預設當日）


@router.post("")
async def fetch(req: FetchRequest):
    end = date.today()
    start = end - timedelta(days=req.days - 1)

    raw = await _fetch_raw(start, end)

    if not raw:
        # 今日資料尚未更新（每日 20:30 更新），改抓昨天
        end = end - timedelta(days=1)
        start = end - timedelta(days=req.days - 1)
        raw = await _fetch_raw(start, end)

    if not raw:
        raise HTTPException(status_code=503, detail="農委會資料暫時無法取得")

    data_date = raw[0]["交易日期"]
    vege = _aggregate(raw, CATEGORY_VEGE)
    result = vege

    if req.include_fruit:
        fruit = _aggregate(raw, CATEGORY_FRUIT)
        result = sorted(vege + fruit, key=lambda x: x["total_volume_kg"], reverse=True)

    return {
        "data_date": data_date,
        "total": min(len(result), req.top_n),
        "items": result[: req.top_n],
    }
