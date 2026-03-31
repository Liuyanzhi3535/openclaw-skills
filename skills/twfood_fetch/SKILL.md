---
name: twfood-fetch
description: 查詢台灣當週盛產蔬菜和水果的批發行情。
             當用戶說「當季食材」「菜價」「水果行情」「規劃菜單」「便宜蔬菜」時使用。
---

## 何時使用

- 需要知道現在什麼蔬果最便宜、最盛產
- 規劃一週菜單前，先查當季食材
- 用戶問「現在什麼菜最便宜」「當季有什麼水果」

## 呼叫方式

```bash
# 只查蔬菜（預設）
curl -X POST http://localhost:8080/skill/twfood-fetch \
  -H "Content-Type: application/json" \
  -d '{"top_n": 10}'

# 含水果
curl -X POST http://localhost:8080/skill/twfood-fetch \
  -H "Content-Type: application/json" \
  -d '{"top_n": 10, "include_fruit": true}'
```

## 參數

| 欄位 | 預設 | 說明 |
|------|------|------|
| `top_n` | 10 | 回傳前 N 筆（依成交量排序） |
| `include_fruit` | false | 是否含水果 |
| `pages` | 1 | 爬幾頁（每頁 10 筆，通常 1 頁就夠） |

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
