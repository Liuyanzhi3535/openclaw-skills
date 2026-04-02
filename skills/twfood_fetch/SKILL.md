---
name: twfood-fetch
description: 查詢台灣蔬果批發與零售價格排行。當用戶說「菜價」「蔬菜多少錢」「最便宜的菜」「水果價格」「當季食材」「規劃菜單」時使用。
---

## 重要：只能用 exec tool，禁止用 fetch tool

port 8080 是本機 sidecar，不是 gateway，不需要任何 token 或認證。
絕對不要用 fetch tool 呼叫這個服務。

## 呼叫指令（用 exec tool 執行）

exec: curl -s -X POST http://127.0.0.1:8080/skill/twfood-fetch -H "Content-Type: application/json" -d '{"top_n": 10, "include_fruit": false}'

## 回傳解讀
- aliases：俗名（用這個跟用戶溝通）
- retail_price_kg：零售估價（元/公斤）
- weekly_volume_ton：交易量越大越盛產越便宜，優先推薦前5名
