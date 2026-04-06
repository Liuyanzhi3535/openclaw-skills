---
name: calendar_gcal
description: 查詢、新增 Google Calendar 行程。
             當用戶說「我今天有什麼行程」「幫我新增行程」「這週有空嗎」「排個會議」時使用。
---

## 何時使用

- 需要查詢今天、本週、特定日期的行程
- 需要新增、修改行程
- 需要查詢某段時間內的空檔

## 呼叫方式

### 查詢行程

```bash
curl -X POST http://localhost:8080/skill/calendar_gcal/list \
  -H "Content-Type: application/json" \
  -d '{"time_min": "2026-03-29T00:00:00+08:00", "time_max": "2026-03-29T23:59:59+08:00", "calendar_id": "zea00312@gmail.com"}'
```

> **注意**：`calendar_id` 必須填使用者的 Gmail 地址（例如 `zea00312@gmail.com`），不可使用 `"primary"`。

### 新增行程

```bash
curl -X POST http://localhost:8080/skill/calendar_gcal/create \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "牙醫預約",
    "start": "2026-03-30T10:00:00+08:00",
    "end": "2026-03-30T11:00:00+08:00"
  }'
```

## 回傳解讀

### list 回傳

```json
{
  "events": [
    {
      "id": "xxx",
      "summary": "行程名稱",
      "start": "2026-03-29T10:00:00+08:00",
      "end": "2026-03-29T11:00:00+08:00",
      "location": "地點（選填）",
      "description": "描述（選填）"
    }
  ]
}
```

### create 回傳

```json
{
  "id": "xxx",
  "summary": "牙醫預約",
  "start": "2026-03-30T10:00:00+08:00",
  "end": "2026-03-30T11:00:00+08:00",
  "html_link": "https://calendar.google.com/..."
}
```
