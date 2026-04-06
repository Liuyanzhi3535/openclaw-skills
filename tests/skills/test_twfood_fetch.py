from datetime import date
from unittest.mock import patch

import httpx
import pytest
import respx

API_URL = "https://data.moa.gov.tw/api/v1/AgriProductsTransType/"

MOCK_VEGE = {
    "RS": "OK",
    "Data": [
        {
            "TransDate": "115.04.02",
            "TcType": "N04",
            "CropCode": "LA1",
            "CropName": "甘藍-初秋",
            "MarketCode": "101",
            "MarketName": "台北一",
            "Upper_Price": 10.0,
            "Middle_Price": 8.0,
            "Lower_Price": 6.0,
            "Avg_Price": 8.5,
            "Trans_Quantity": 200000.0,
        },
        {
            "TransDate": "115.04.02",
            "TcType": "N04",
            "CropCode": "LA1",
            "CropName": "甘藍-初秋",
            "MarketCode": "102",
            "MarketName": "台北二",
            "Upper_Price": 11.0,
            "Middle_Price": 9.0,
            "Lower_Price": 7.0,
            "Avg_Price": 9.0,
            "Trans_Quantity": 100000.0,
        },
        {
            "TransDate": "115.04.02",
            "TcType": "N04",
            "CropCode": "FB1",
            "CropName": "花椰菜-青梗",
            "MarketCode": "101",
            "MarketName": "台北一",
            "Upper_Price": 20.0,
            "Middle_Price": 15.0,
            "Lower_Price": 10.0,
            "Avg_Price": 15.0,
            "Trans_Quantity": 50000.0,
        },
    ],
}

MOCK_FRUIT = {
    "RS": "OK",
    "Data": [
        {
            "TransDate": "115.04.02",
            "TcType": "N05",
            "CropCode": "11",
            "CropName": "椰子",
            "MarketCode": "101",
            "MarketName": "台北一",
            "Upper_Price": 20.0,
            "Middle_Price": 12.0,
            "Lower_Price": 9.0,
            "Avg_Price": 12.0,
            "Trans_Quantity": 10000.0,
        },
    ],
}


@pytest.fixture
def mock_today():
    with patch("skills.twfood_fetch.main.date") as mock_date:
        mock_date.today.return_value = date(2026, 4, 2)
        mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
        yield mock_date


@pytest.fixture
def mock_moa(mock_today):
    with respx.mock(assert_all_called=False) as mock:
        mock.get(API_URL, params__contains={"TcType": "N04"}).mock(
            return_value=httpx.Response(200, json=MOCK_VEGE)
        )
        mock.get(API_URL, params__contains={"TcType": "N05"}).mock(
            return_value=httpx.Response(200, json=MOCK_FRUIT)
        )
        yield mock


async def test_fetch_vege_only(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 200
    body = response.json()
    items = body["items"]
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
    expected = round((200000 * 8.5 + 100000 * 9.0) / 300000, 1)
    assert items[0]["avg_price_kg"] == expected


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
        mock.get(API_URL).mock(return_value=httpx.Response(500))
        response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 502


async def test_response_has_period(client, mock_moa):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 5})
    body = response.json()
    assert "period" in body
    assert "data_date" in body
