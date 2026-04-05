---
name: twfood-fetch
description: 查詢台灣蔬果批發與零售價格排行。當用戶說「菜價」「蔬菜多少錢」「最便宜的菜」「水果價格」「當季食材」「規劃菜單」時使用。
---

## 重要：只能用 exec tool，禁止用 fetch tool

port 8080 是本機 sidecar，不是 gateway，不需要任何 token 或認證。
絕對不要用 fetch tool 呼叫這個服務。

## 呼叫指令（用 exec tool 執行）

只查蔬菜：
exec: curl -s -X POST http://127.0.0.1:8080/skill/twfood-fetch -H "Content-Type: application/json" -d '{"top_n": 10}'

含水果：
exec: curl -s -X POST http://127.0.0.1:8080/skill/twfood-fetch -H "Content-Type: application/json" -d '{"top_n": 10, "include_fruit": true}'

## 參數

| 欄位 | 預設 | 說明 |
|------|------|------|
| top_n | 10 | 回傳前 N 筆 |
| include_fruit | false | true 時同時查水果，與蔬菜合併排行 |
| days | 7 | 查最近幾天均值（預設 7 天，自動跳過休市日） |

## 回傳格式

```json
{
  "data_date": "115.04.02",
  "total": 10,
  "items": [
    {
      "name": "甘藍-初秋",
      "avg_price_kg": 8.5,
      "total_volume_kg": 312000,
      "market_count": 12
    }
  ]
}
```

## 回傳解讀

- items 已依 total_volume_kg 由大到小排序（交易量越大越盛產越便宜）
- name：作物名稱，跟用戶溝通時可簡化（「甘藍-初秋」說成「高麗菜」）
- avg_price_kg：加權平均批發價（元/公斤），零售約為此價 × 1.5–2 倍
- total_volume_kg：全台各市場當日總交易量（公斤），優先推薦前 5 名
- data_date：資料日期（民國年），農委會每日 20:30 更新
