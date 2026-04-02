---
name: twfood-fetch
description: 查詢台灣蔬果批發與零售價格排行。
             當用戶說「菜價」「蔬菜多少錢」「最便宜的菜」「水果價格」「當季食材」「規劃菜單」時使用。
---

## 何時使用

- 查詢本週台灣蔬菜/水果批發、零售價格
- 查詢交易量排行
- 規劃菜單前查詢當季便宜食材

## 呼叫方式

使用 fetch tool 發送 POST 請求：

URL: http://localhost:8080/skill/twfood-fetch
Method: POST
Content-Type: application/json
Body: {"top_n": 10, "include_fruit": false}

參數（皆選填）：
- top_n：回傳筆數，預設 10
- include_fruit：是否含水果，預設 false
- pages：爬幾頁，預設 1

## 回傳解讀

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

- `weekly_volume_ton`：越大越盛產，優先推薦前 5 名
- `retail_price_kg`：零售估價（元/公斤），跟用戶溝通用這個
- `aliases`：用俗名跟用戶溝通（說「高麗菜」而非「甘藍-初秋」）
