import re

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/skill/twfood-fetch")

BASE_URL = "https://www.twfood.cc"

# 符合 vege_price card 的 pattern
_CARD_RE = re.compile(
    r'<div class="col-xs-6[^"]*vege_price".*?(?=<div class="col-xs-6|$)',
    re.DOTALL,
)
_RANK_RE = re.compile(r"推薦No:\s*(\d+)")
_NAME_RE = re.compile(r"推薦No:\s*\d+\s*([\w\u4e00-\u9fff]+)")
_ALIAS_RE = re.compile(r"\(([^)]+)\)")
_PRICE_RE = re.compile(r'<span class="text-price">\s*([\d.]+)\s*</span>')
_UNIT_RE = re.compile(r'<th class="vege_chart_th_unit">\s*([^<]+?)\s*</th>')
_VOLUME_RE = re.compile(r"成交量:.*?<span class=\"text-price\">\s*([\d,]+)\s*</span>", re.DOTALL)


def _parse_card(card_html: str) -> dict | None:
    rank_m = _RANK_RE.search(card_html)
    name_m = _NAME_RE.search(card_html)
    if not rank_m or not name_m:
        return None

    # 名稱：取推薦No後第一段文字，去除括號內容
    raw_name = name_m.group(1).strip()
    name = re.sub(r"[（(].*", "", raw_name).strip("，,- ")

    # 俗名別名
    raw_aliases = _ALIAS_RE.findall(card_html)
    raw_aliases = [a for a in raw_aliases if "元" not in a and "公" not in a]
    aliases = []
    for a in raw_aliases:
        aliases.extend(re.split(r"[,，]", a))

    prices = _PRICE_RE.findall(card_html)
    units = _UNIT_RE.findall(card_html)

    wholesale_kg = None
    retail_kg = None
    volume_ton = None

    # 依序對應：批發/公斤、批發/台斤、零售/公斤、零售/台斤、成交量
    for price, unit in zip(prices, units):
        unit = unit.strip()
        if "元/公斤" in unit and wholesale_kg is None:
            wholesale_kg = float(price)
        elif "元/公斤" in unit and retail_kg is None:
            retail_kg = float(price)

    # 成交量單獨抓
    vol_m = _VOLUME_RE.search(card_html)
    if vol_m:
        volume_ton = int(vol_m.group(1).replace(",", ""))

    return {
        "rank": int(rank_m.group(1)),
        "name": name,
        "aliases": [a.strip() for a in aliases if a.strip()],
        "wholesale_price_kg": wholesale_kg,
        "retail_price_kg": retail_kg,
        "weekly_volume_ton": volume_ton,
    }


async def _fetch_items(category: str, pages: int) -> list[dict]:
    items = []
    async with httpx.AsyncClient(timeout=10) as client:
        for page in range(1, pages + 1):
            url = f"{BASE_URL}/{category}?page={page}&per-page=10"
            try:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
            except httpx.HTTPError as e:
                raise HTTPException(status_code=502, detail=f"twfood.cc 請求失敗: {e}")

            for card in _CARD_RE.finditer(resp.text):
                item = _parse_card(card.group())
                if item:
                    items.append(item)
    return items


# ---------- endpoint ----------

class FetchRequest(BaseModel):
    top_n: int = 10
    include_fruit: bool = False
    pages: int = 1


@router.post("")
async def fetch(req: FetchRequest):
    items = await _fetch_items("vege", req.pages)

    if req.include_fruit:
        fruit_items = await _fetch_items("fruit", req.pages)
        items.extend(fruit_items)

    # 依成交量排序（越大越盛產），volume 為 None 的排最後
    items.sort(key=lambda x: x["weekly_volume_ton"] or 0, reverse=True)
    items = items[: req.top_n]

    return {"total": len(items), "items": items}
