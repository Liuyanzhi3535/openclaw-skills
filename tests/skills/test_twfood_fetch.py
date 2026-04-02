import pytest
import respx
import httpx
from unittest.mock import patch
from datetime import date

MOA_URL = "https://data.moa.gov.tw/Service/OpenData/FromM/FarmTransData.aspx"

MOCK_RESPONSE = [
    {
        "交易日期": "115.04.02",
        "種類代碼": "N04",
        "作物代號": "LA1",
        "作物名稱": "甘藍-初秋",
        "市場代號": "101",
        "市場名稱": "台北一",
        "上價": 10.0,
        "中價": 8.0,
        "下價": 6.0,
        "平均價": 8.5,
        "交易量": 200000.0,
    },
    {
        "交易日期": "115.04.02",
        "種類代碼": "N04",
        "作物代號": "LA1",
        "作物名稱": "甘藍-初秋",
        "市場代號": "102",
        "市場名稱": "台北二",
        "上價": 11.0,
        "中價": 9.0,
        "下價": 7.0,
        "平均價": 9.0,
        "交易量": 100000.0,
    },
    {
        "交易日期": "115.04.02",
        "種類代碼": "N04",
        "作物代號": "FB1",
        "作物名稱": "花椰菜-青梗",
        "市場代號": "101",
        "市場名稱": "台北一",
        "上價": 20.0,
        "中價": 15.0,
        "下價": 10.0,
        "平均價": 15.0,
        "交易量": 50000.0,
    },
    {
        "交易日期": "115.04.02",
        "種類代碼": "N05",
        "作物代號": "11",
        "作物名稱": "椰子",
        "市場代號": "101",
        "市場名稱": "台北一",
        "上價": 20.0,
        "中價": 12.0,
        "下價": 9.0,
        "平均價": 12.0,
        "交易量": 10000.0,
    },
]


@pytest.fixture
def mock_today():
    with patch("skills.twfood_fetch.main.date") as mock_date:
        mock_date.today.return_value = date(2026, 4, 2)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        yield mock_date


@pytest.fixture
def mock_moa(mock_today):
    with respx.mock(assert_all_called=False) as mock:
        mock.get(MOA_URL).mock(return_value=httpx.Response(200, json=MOCK_RESPONSE))
        yield mock


async def test_fetch_vege_only(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["data_date"] == "115.04.02"
    items = body["items"]
    # 只有蔬菜 2 種
    assert body["total"] == 2
    names = [i["name"] for i in items]
    assert "椰子" not in names
    # 甘藍交易量最大排第一
    assert items[0]["name"] == "甘藍-初秋"
    assert items[0]["total_volume_kg"] == 300000
    assert items[0]["market_count"] == 2


async def test_fetch_weighted_avg_price(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    items = response.json()["items"]
    # 甘藍加權均價：(200000*8.5 + 100000*9.0) / 300000 = 8.67
    assert items[0]["avg_price_kg"] == round((200000 * 8.5 + 100000 * 9.0) / 300000, 1)


async def test_fetch_include_fruit(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10, "include_fruit": True})
    assert response.status_code == 200
    names = [i["name"] for i in response.json()["items"]]
    assert "椰子" in names


async def test_fetch_top_n(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 1})
    assert response.json()["total"] == 1


async def test_fetch_upstream_error(client, mock_today):
    with respx.mock(assert_all_called=False) as mock:
        mock.get(MOA_URL).mock(return_value=httpx.Response(500))
        response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 502


async def test_fetch_fallback_to_yesterday(client, mock_today):
    """當日無資料時自動改抓昨日。"""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=MOCK_RESPONSE)

    with respx.mock(assert_all_called=False) as mock:
        mock.get(MOA_URL).mock(side_effect=side_effect)
        response = await client.post("/skill/twfood-fetch", json={"top_n": 10})

    assert response.status_code == 200
    assert call_count == 2
