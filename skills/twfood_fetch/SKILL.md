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
| include_fruit | false | true 時同時查水果 |
| pages | 1 | 爬幾頁（每頁 10 筆） |

## 回傳格式

```json
{
  "total": 10,
  "items": [
    {
      "rank": 1,
      "name": "甘藍",
      "aliases": ["高麗菜", "捲心菜"],
      "wholesale_price_kg": 6.4,
      "retail_price_kg": 13.0,
      "weekly_volume_ton": 3942
    }
  ]
}
```

## 回傳解讀

- items 已依 weekly_volume_ton 由大到小排序（越大越盛產越便宜）
- aliases：俗名，用這個跟用戶溝通（說「高麗菜」而非「甘藍」）
- retail_price_kg：零售估價（元/公斤），用這個估算採購成本
- weekly_volume_ton：本週交易量（公噸），優先推薦前 5 名
