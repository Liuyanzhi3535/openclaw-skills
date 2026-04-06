---
name: price-compare
description: 比較 PChome 與 MOMO 的商品價格，找出最便宜的選擇。
             當用戶說「幫我比價」「MOMOPC」「哪裡買比較便宜」「PChome 還是 MOMO」時使用。
---

## 重要：只能用 exec tool，禁止用 fetch tool

port 8080 是本機 sidecar，不是 gateway，不需要任何 token 或認證。

## 呼叫指令（用 exec tool 執行）

exec: curl -s -X POST http://127.0.0.1:8080/skill/price-compare -H "Content-Type: application/json" -d '{"keyword": "萬國旅行充", "top_n": 5}'

## 參數

| 欄位 | 預設 | 說明 |
|------|------|------|
| keyword | 必填 | 搜尋關鍵字 |
| top_n | 5 | 每個平台回傳幾筆 |

## 回傳格式

```json
{
  "keyword": "萬國旅行充",
  "cheapest": {
    "platform": "PChome",
    "name": "商品名稱",
    "price": 524,
    "original_price": 799,
    "discount": 34,
    "url": "https://24h.pchome.com.tw/prod/..."
  },
  "savings": 275,
  "pchome": [...],
  "momo": [...]
}
```

## 回傳解讀

- cheapest：全站最低價商品
- savings：兩平台最低價的價差（元），越大表示選對平台越划算
- discount：折扣幅度（%），0 表示無折扣
- pchome / momo：各平台前 top_n 筆，依價格由低至高排列
- 建議先看 cheapest，再看 savings 決定去哪個平台