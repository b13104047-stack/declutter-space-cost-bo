# 斷捨離空間成本 Bot

LINE Bot MVP：使用者輸入房租、房價或粗估條件後，Bot 會把物品佔用空間換算成租金成本或房屋資產價值，提醒「不丟東西也有持有成本」。

## 技術架構

- Python 3.11+
- Flask
- LINE Messaging API
- line-bot-sdk v3
- gunicorn
- python-dotenv
- Render Web Service 部署

## 專案結構

```text
.
├── app.py
├── space_cost.py
├── tests/
│   └── test_space_cost.py
├── requirements.txt
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md
```

## 環境變數

不要把真實 token 或 secret 寫進 repo。請在本機建立 `.env`：

```env
LINE_CHANNEL_SECRET=你的 LINE Channel Secret
LINE_CHANNEL_ACCESS_TOKEN=你的 LINE Channel Access Token
```

Render 上也要設定同樣兩個環境變數：

- `LINE_CHANNEL_SECRET`
- `LINE_CHANNEL_ACCESS_TOKEN`

## 本機執行

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Health check：

```bash
curl http://localhost:5000/
```

預期回覆：

```text
斷捨離空間成本 Bot is running.
```

核心計算測試：

```bash
python -m unittest discover -s tests
```

如果要讓 LINE 打到本機，可使用 ngrok 或其他 tunnel，並把 webhook 設成：

```text
https://你的-tunnel-domain/callback
```

## Render 部署

1. 建立 GitHub repo。
2. Push 程式碼到 GitHub。
3. 在 Render 建立 `Web Service`，連接該 GitHub repo。
4. Build Command 設定：

```bash
pip install -r requirements.txt
```

5. Start Command 設定：

```bash
gunicorn app:app
```

6. 在 Render 的 Environment 設定：

```text
LINE_CHANNEL_SECRET
LINE_CHANNEL_ACCESS_TOKEN
```

7. 部署完成後，取得 Render 網址，例如：

```text
https://your-service-name.onrender.com
```

## LINE Developers Console 設定

Webhook URL 填：

```text
https://你的-render網址.onrender.com/callback
```

接著確認：

- 啟用 `Use webhook`。
- 關閉 LINE 官方帳號自動回覆，避免干擾 webhook。
- 如有 Greeting message 或 Auto-response message，MVP 測試時建議先關閉。

## 使用方式

教學訊息：

```text
開始
```

或：

```text
help
```

或：

```text
說明
```

目前支援三種模式。

月租模式：

```text
月租 18000 坪數 8 長 60 寬 40
```

也支援空格不一致：

```text
月租18000 坪數8 長60 寬40
```

房價模式：

```text
房價 18000000 坪數 25 長 100 寬 60
```

粗估模式：

```text
估算 台北市 大安區 套房 8 長60 寬40
```

粗估模式使用程式內建的簡易每坪月租表，不串外部 API。回覆會標註：

```text
這是粗估，不代表實際租金或房價行情。
```

長、寬預設單位是公分。

## 手動測試案例

1. 輸入 `開始`，應回覆教學訊息。
2. 輸入 `月租 18000 坪數 8 長 60 寬 40`，應回覆約每月 163 元、每年 1,960 元。
3. 輸入 `月租18000 坪數8 長60 寬40`，結果應與上一筆相同。
4. 輸入 `房價 18000000 坪數 25 長 100 寬 60`，應回覆物品佔用價值約 130,679 元。
5. 輸入 `估算 台北市 大安區 套房 8 長60 寬40`，應回覆粗估提示與每月、每年空間成本。
6. 輸入 `月租 18000 長 60 寬 40`，應提示缺少 `坪數`。
7. 輸入 `月租 0 坪數 8 長 60 寬 40`，應提示數字必須大於 0。
8. 輸入貼圖、圖片或無法解析文字，應提示目前 MVP 只支援文字或請使用正確格式。

自動測試：

```bash
python -m unittest discover -s tests
```

## 計算公式

月租模式：

- 物品平方公尺 = 長(cm) × 寬(cm) ÷ 10000
- 物品坪數 = 物品平方公尺 ÷ 3.3058
- 每坪每月租金 = 月租 ÷ 房屋坪數
- 物品每月空間成本 = 每坪每月租金 × 物品坪數
- 物品每年空間成本 = 每月成本 × 12

房價模式：

- 物品坪數 = 長(cm) × 寬(cm) ÷ 10000 ÷ 3.3058
- 每坪房價 = 房價 ÷ 房屋坪數
- 物品佔用價值 = 每坪房價 × 物品坪數

粗估模式：

- 物品坪數 = 長(cm) × 寬(cm) ÷ 10000 ÷ 3.3058
- 每月空間成本 = 內建每坪月租估算值 × 物品坪數
- 每年空間成本 = 每月成本 × 12

粗估 fallback 每坪月租：

- 台北市：1,800 元
- 新北市：1,300 元
- 桃園市：900 元
- 台中市：1,000 元
- 台南市：800 元
- 高雄市：850 元
- 其他：700 元

## 安全注意事項

- 不要 commit `.env`。
- 不要把 LINE token 或 secret 寫死在 `app.py`。
- LINE webhook 會驗證 `X-Line-Signature`，signature 不正確會回傳 `400`。
- Render 環境變數只設定在服務後台，不要寫進 README 以外的真實值。
- 若 token 外洩，請立即到 LINE Developers Console 重新發行 Channel Access Token。
