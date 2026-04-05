from collections import defaultdict
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/skill/twfood-fetch")

API_URL = "https://data.moa.gov.tw/api/v1/AgriProductsTransType/"

CATEGORY_VEGE = "N04"
CATEGORY_FRUIT = "N05"


def _to_roc(d: date) -> str:
    """轉民國年格式，例：2026-04-02 → 115.04.02"""
    return f"{d.year - 1911}.{d.month:02d}.{d.day:02d}"


async def _fetch_raw(start: date, end: date, tc_type: str) -> list[dict]:
    params = {
        "Start_time": _to_roc(start),
        "End_time": _to_roc(end),
        "TcType": tc_type,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(API_URL, params=params, headers={"accept": "application/json"})
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"農委會 API 請求失敗: {e}")

    body = resp.json()
    if body.get("RS") != "OK":
        return []
    return body.get("Data") or []


def _aggregate(records: list[dict]) -> list[dict]:
    """同一作物跨市場加總交易量、加權平均價格。"""
    by_crop: dict[str, dict] = defaultdict(lambda: {
        "total_volume": 0.0,
        "weighted_price_sum": 0.0,
        "markets": set(),
    })

    for r in records:
        name = r["CropName"]
        vol = r["Trans_Quantity"] or 0
        price = r["Avg_Price"] or 0
        if name == "休市" or vol == 0:
            continue
        by_crop[name]["total_volume"] += vol
        by_crop[name]["weighted_price_sum"] += vol * price
        by_crop[name]["markets"].add(r["MarketName"])

    result = []
    for name, agg in by_crop.items():
        vol = agg["total_volume"]
        avg_price = agg["weighted_price_sum"] / vol if vol > 0 else 0
        result.append({
            "name": name,
            "avg_price_kg": round(avg_price, 1),
            "total_volume_kg": int(vol),
            "market_count": len(agg["markets"]),
        })

    result.sort(key=lambda x: x["total_volume_kg"], reverse=True)
    return result


# ---------- endpoint ----------

class FetchRequest(BaseModel):
    top_n: int = 10
    include_fruit: bool = False
    days: int = 7  # 查最近幾天，預設 7 天避開休市日


@router.post("")
async def fetch(req: FetchRequest):
    end = date.today()
    start = end - timedelta(days=req.days - 1)

    vege_raw = await _fetch_raw(start, end, CATEGORY_VEGE)
    vege = _aggregate(vege_raw)

    if not vege:
        raise HTTPException(status_code=503, detail="農委會資料暫時無法取得，請稍後再試")

    if req.include_fruit:
        fruit_raw = await _fetch_raw(start, end, CATEGORY_FRUIT)
        fruit = _aggregate(fruit_raw)
        result = sorted(vege + fruit, key=lambda x: x["total_volume_kg"], reverse=True)
    else:
        result = vege

    data_date = vege_raw[-1]["TransDate"] if vege_raw else _to_roc(end)

    return {
        "data_date": data_date,
        "period": f"{_to_roc(start)} ~ {_to_roc(end)}",
        "total": min(len(result), req.top_n),
        "items": result[: req.top_n],
    }
