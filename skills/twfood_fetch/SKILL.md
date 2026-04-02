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

使用 exec tool 執行以下指令：

```bash
curl -s -X POST http://localhost:8080/skill/twfood-fetch \
  -H "Content-Type: application/json" \
  -d '{"top_n": 10, "include_fruit": false}'
```

## 回傳解讀

- name：蔬菜名稱
- aliases：俗名（用這個跟用戶溝通）
- wholesale_price_kg：批發價（元/公斤）
- retail_price_kg：零售價（元/公斤），用這個估算採購成本
- weekly_volume_ton：本週交易量（公噸），越大越盛產越便宜，優先推薦前5名
