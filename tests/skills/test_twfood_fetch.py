import pytest
import respx
import httpx


VEGE_HTML = """
<div class="col-xs-6 col-sm-6 col-md-12 vege_price" >
  <h4 class="text-left h4">
    <a href="/vege/LA1/甘藍-初秋(高麗菜,捲心菜)">
      <em class="glyphicon glyphicon-check"></em>
      推薦No: 1  甘藍-初秋  (高麗菜,捲心菜)
    </a>
  </h4>
  <table class="table table-hover">
    <tr><th class="text-left" colspan="2">本週平均批發價:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">6.4</span></th>
        <th class="vege_chart_th_unit">(元/公斤)</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">3.8</span></th>
        <th class="vege_chart_th_unit">(元/台斤)</th></tr>
    <tr><th class="text-left" colspan="2">預估零售價:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">13</span></th>
        <th class="vege_chart_th_unit">(元/公斤)</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">8</span></th>
        <th class="vege_chart_th_unit">(元/台斤)</th></tr>
    <tr><th class="text-left" colspan="2">成交量:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">3942</span></th>
        <th class="vege_chart_th_unit">公噸</th></tr>
  </table>
</div>
<div class="col-xs-6 col-sm-6 col-md-12 vege_price" >
  <h4 class="text-left h4">
    <a href="/vege/FB1/花椰菜-青梗(青花菜)">
      <em class="glyphicon glyphicon-check"></em>
      推薦No: 2  花椰菜-青梗  (青花菜)
    </a>
  </h4>
  <table class="table table-hover">
    <tr><th class="text-left" colspan="2">本週平均批發價:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">14.5</span></th>
        <th class="vege_chart_th_unit">(元/公斤)</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">8.7</span></th>
        <th class="vege_chart_th_unit">(元/台斤)</th></tr>
    <tr><th class="text-left" colspan="2">預估零售價:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">29</span></th>
        <th class="vege_chart_th_unit">(元/公斤)</th></tr>
    <tr><th class="text-left" colspan="2">成交量:</th></tr>
    <tr><th class="text-right vege_chart_th_number"><span class="text-price">1200</span></th>
        <th class="vege_chart_th_unit">公噸</th></tr>
  </table>
</div>
"""


@pytest.fixture
def mock_twfood():
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.twfood.cc/vege?page=1").mock(
            return_value=httpx.Response(200, text=VEGE_HTML)
        )
        mock.get("https://www.twfood.cc/fruit?page=1").mock(
            return_value=httpx.Response(200, text="")
        )
        yield mock


async def test_fetch_returns_items(client, mock_twfood):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    items = body["items"]
    # 依成交量排序，高麗菜（3942）應在第一
    assert items[0]["name"] == "甘藍"
    assert items[0]["weekly_volume_ton"] == 3942
    assert items[0]["wholesale_price_kg"] == 6.4
    assert items[0]["retail_price_kg"] == 13.0
    assert "高麗菜" in items[0]["aliases"]


async def test_fetch_top_n_limits_results(client, mock_twfood):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 1})
    assert response.status_code == 200
    assert response.json()["total"] == 1


async def test_fetch_include_fruit(client, mock_twfood):
    response = await client.post("/skill/twfood-fetch", json={"top_n": 10, "include_fruit": True})
    assert response.status_code == 200
    # fruit page 回傳空 HTML，只有蔬菜 2 筆
    assert response.json()["total"] == 2


async def test_fetch_upstream_error(client):
    with respx.mock(assert_all_called=False) as mock:
        mock.get("https://www.twfood.cc/vege?page=1").mock(
            return_value=httpx.Response(500)
        )
        response = await client.post("/skill/twfood-fetch", json={"top_n": 10})
    assert response.status_code == 502
