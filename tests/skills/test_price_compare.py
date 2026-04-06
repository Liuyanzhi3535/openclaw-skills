import json

import httpx
import pytest
import respx

PCHOME_URL = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
MOMO_URL = "https://www.momoshop.com.tw/search/%E8%90%AC%E5%9C%8B%E6%97%85%E8%A1%8C%E5%85%85"

MOCK_PCHOME = {
    "totalRows": 2,
    "prods": [
        {
            "Id": "DYBACY-A900HS55L",
            "name": "QC3.0+PD20W快充 萬國旅行充電器",
            "price": 524,
            "originPrice": 799,
        },
        {
            "Id": "DYBA18-A900G8OEF",
            "name": "全新萬國旅行充電器極速支援雙PD雙QC",
            "price": 799,
            "originPrice": 799,
        },
    ],
}

MOCK_MOMO_RSC = (
    '"goodsInfoList":['
    '{"goodsCode":"13746361","goodsName":"【DTAudio】70W萬國旅行充",'
    '"goodsPrice":"$$1,181","goodsPriceOri":"$$2,999"},'
    '{"goodsCode":"11824025","goodsName":"【DTAudio】PD20W 萬國旅行充",'
    '"goodsPrice":"$$599","goodsPriceOri":"$$999"}'
    '],"filterInfoList":'
)


@pytest.fixture
def mock_shops():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(PCHOME_URL).mock(return_value=httpx.Response(200, json=MOCK_PCHOME))
        mock.get(url__regex=r"momoshop\.com\.tw/search/").mock(
            return_value=httpx.Response(200, text=MOCK_MOMO_RSC)
        )
        yield mock


async def test_compare_returns_both_platforms(client, mock_shops):
    response = await client.post(
        "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 5}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["keyword"] == "萬國旅行充"
    assert len(body["pchome"]) == 2
    assert len(body["momo"]) == 2


async def test_cheapest_is_lowest_price(client, mock_shops):
    response = await client.post(
        "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 5}
    )
    body = response.json()
    cheapest = body["cheapest"]
    all_prices = [p["price"] for p in body["pchome"] + body["momo"]]
    assert cheapest["price"] == min(all_prices)


async def test_savings_calculated(client, mock_shops):
    response = await client.post(
        "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 5}
    )
    body = response.json()
    # PChome min=524, MOMO min=599, diff=75
    assert body["savings"] == 75


async def test_discount_percentage(client, mock_shops):
    response = await client.post(
        "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 5}
    )
    pchome = response.json()["pchome"]
    # 524/799 → 34% off
    assert pchome[0]["discount"] == 34


async def test_top_n_limits_results(client, mock_shops):
    response = await client.post(
        "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 1}
    )
    body = response.json()
    assert len(body["pchome"]) == 1
    assert len(body["momo"]) == 1


async def test_pchome_upstream_error(client):
    with respx.mock(assert_all_called=False) as mock:
        mock.get(PCHOME_URL).mock(return_value=httpx.Response(500))
        mock.get(url__regex=r"momoshop\.com\.tw/search/").mock(
            return_value=httpx.Response(200, text=MOCK_MOMO_RSC)
        )
        response = await client.post(
            "/skill/price-compare", json={"keyword": "萬國旅行充", "top_n": 5}
        )
    assert response.status_code == 502
