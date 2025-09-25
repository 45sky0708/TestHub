# TestHub

此專案用於規劃 Connect Hub 平台的需求與 AI 導入藍圖。主要文件如下：

- `requirements.md`：以 EARS 格式撰寫的功能與非功能需求。
- `ai-dlc-adoption-plan.md`：導入 AI-Driven Development Lifecycle 的階段性建議。
- `design-phase-documents.md`：Design 階段的文件產出指引與審查節點。
- `design-architecture-reference.md`：提供系統架構、流程與序列圖模板，協助設計文件撰寫。
- `design.md`：系統設計重點與架構說明，支援開發前的整體對齊。
- `mvp-development-plan.md`：基於預設場景的 MVP 開發規劃、系統架構與交付里程碑。

後續開發可依據上述文件逐步細化使用者流程、技術設計與 AI 功能實作。

## 開發啟動程式碼

- `app/models.py` 與 `app/service.py`：定義 Connect Hub MVP 的核心領域模型與應用服務，涵蓋活動管理、報名（含重複註冊防護與取消流程）、AI 推薦與人才媒合邏輯。
- `app/main.py`：提供可快速載入範例資料的 helper，方便團隊本地驗證流程或接上 API 層。
- `app/web.py`：使用標準庫組成的 WSGI 應用，提供 MVP 面板與 JSON API，便於快速部署或串接。
- `tests/test_service.py`：覆蓋主要服務操作（活動 CRUD、報名/取消、推薦、媒合狀態與儀表板指標），做為持續開發的安全網。

### 啟動 MVP Demo 畫面

1. 建議建立虛擬環境，並安裝專案：

   ```bash
   pip install -e .
   ```

2. 透過標準庫啟動 WSGI 伺服器並開啟瀏覽器：

   ```bash
   python -m app.web
   ```

   預設伺服器會啟動於 `http://127.0.0.1:8000/`，可看到即時指標、即將舉辦與所有活動清單，並可透過 `/api/events`、`/api/dashboard` 取得 JSON 資訊。

### 執行測試

```bash
pytest
```