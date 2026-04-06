import asyncio
import re
from urllib.parse import quote

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/skill/price-compare")

PCHOME_URL = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
MOMO_URL = "https://www.momoshop.com.tw/search/{keyword}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-TW,zh;q=0.9",
}

MOMO_RSC_HEADERS = {
    **HEADERS,
    "RSC": "1",
    "Next-Router-State-Tree": (
        '%5B%22%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D'
    ),
}


def _parse_price(raw: str) -> int:
    """移除 $$ 符號與逗號，轉成整數。"""
    return int(re.sub(r"[^\d]", "", raw or "0") or 0)


async def _search_pchome(client: httpx.AsyncClient, keyword: str, top_n: int) -> list[dict]:
    try:
        resp = await client.get(
            PCHOME_URL,
            params={"q": keyword, "page": 1, "sort": "rnk/dc"},
            headers=HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PChome 請求失敗: {e}")

    prods = resp.json().get("prods", [])
    result = []
    for p in prods[:top_n]:
        price = p.get("price", 0)
        orig = p.get("originPrice", price)
        pid = p.get("Id", "")
        result.append({
            "platform": "PChome",
            "name": p.get("name", ""),
            "price": price,
            "original_price": orig,
            "discount": round((1 - price / orig) * 100) if orig and orig > price else 0,
            "url": f"https://24h.pchome.com.tw/prod/{pid}",
        })
    return result


async def _search_momo(client: httpx.AsyncClient, keyword: str, top_n: int) -> list[dict]:
    url = MOMO_URL.format(keyword=quote(keyword))
    try:
        resp = await client.get(url, headers=MOMO_RSC_HEADERS, timeout=10, follow_redirects=True)
        resp.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"MOMO 請求失敗: {e}")

    content = resp.text
    import json

    start_marker = '"goodsInfoList":['
    start = content.find(start_marker)
    if start == -1:
        return []

    # 用括號計數找對應的 ] 結尾
    arr_start = start + len(start_marker) - 1
    depth = 0
    arr_end = arr_start
    for i, ch in enumerate(content[arr_start:], arr_start):
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                arr_end = i
                break

    try:
        items = json.loads(content[arr_start : arr_end + 1])
    except Exception:
        return []

    result = []
    for item in items[:top_n]:
        price = _parse_price(item.get("goodsPrice", "0"))
        orig = _parse_price(item.get("goodsPriceOri", "0"))
        code = item.get("goodsCode", "")
        result.append({
            "platform": "MOMO",
            "name": item.get("goodsName", ""),
            "price": price,
            "original_price": orig if orig > price else price,
            "discount": round((1 - price / orig) * 100) if orig and orig > price else 0,
            "url": f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={code}",
        })
    return result


# ---------- endpoint ----------


class CompareRequest(BaseModel):
    keyword: str
    top_n: int = 5  # 每平台回傳筆數


@router.post("")
async def compare(req: CompareRequest):
    async with httpx.AsyncClient() as client:
        pchome_results, momo_results = await asyncio.gather(
            _search_pchome(client, req.keyword, req.top_n),
            _search_momo(client, req.keyword, req.top_n),
        )

    all_results = pchome_results + momo_results
    all_results.sort(key=lambda x: x["price"])

    cheapest = all_results[0] if all_results else None
    pchome_min = min((p["price"] for p in pchome_results), default=None)
    momo_min = min((p["price"] for p in momo_results), default=None)

    savings = None
    if pchome_min and momo_min:
        savings = abs(pchome_min - momo_min)

    return {
        "keyword": req.keyword,
        "cheapest": cheapest,
        "savings": savings,
        "pchome": pchome_results,
        "momo": momo_results,
    }