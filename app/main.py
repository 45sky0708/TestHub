from __future__ import annotations

from datetime import timedelta

from .models import SurfaceFeature, SurfaceSection
from .service import ConnectHubService, utcnow


def bootstrap_demo_service() -> ConnectHubService:
    """Seed a service instance with sample events for local exploration."""
    service = ConnectHubService()
    now = utcnow()
    service.create_event(
        name="Connect Hub Kickoff",
        category="workshop",
        mode="onsite",
        start_at=now + timedelta(days=7),
        end_at=now + timedelta(days=7, hours=2),
        capacity=50,
        location="Taipei",
        tags=["devrel", "community"],
        description="Vision alignment and onboarding workshop.",
    )
    service.create_event(
        name="AI Matching Lab",
        category="lab",
        mode="online",
        start_at=now + timedelta(days=10),
        end_at=now + timedelta(days=10, hours=2),
        capacity=40,
        location="Zoom",
        tags=["ai", "matching"],
        description="Hands-on AI matching experiments.",
    )

    service.configure_surface_blueprint(
        frontend=SurfaceSection(
            title="前台體驗",
            summary="參與者探索活動與技術資源的入口，並透過 AI 獲得個人化建議。",
            features=[
                SurfaceFeature(
                    name="網站首頁",
                    description="呈現 Connect Hub 主視覺、MVP 關鍵價值與活動亮點。",
                    highlights=["主題英雄區", "營運重點導覽", "快速 CTA"],
                ),
                SurfaceFeature(
                    name="活動列表",
                    description="依場景與狀態分類活動，協助參與者快速篩選。",
                    ai_enabled=True,
                    highlights=["Workshop/Matchmaking 標籤", "報名中/已截止狀態", "AI 推薦排序"],
                ),
                SurfaceFeature(
                    name="個人介面",
                    description="整合報名紀錄、待辦任務與 AI 推薦媒合。",
                    ai_enabled=True,
                    highlights=["已報名活動追蹤", "回饋任務提示", "AI 媒合建議"],
                ),
                SurfaceFeature(
                    name="技術資源",
                    description="提供開發者入門資源、API 文件與最新版本資訊。",
                    highlights=["Onboarding Kit", "API Docs", "Release Notes (Medium)"],
                ),
            ],
        ),
        backend=SurfaceSection(
            title="後台營運",
            summary="支援營運團隊掌握活動流程、社群媒合與效益分析的管理後台。",
            features=[
                SurfaceFeature(
                    name="活動管理",
                    description="維護活動模板、時程與容量設定，並控管報名流程。",
                    highlights=["模板與排程", "票券與名額管理", "講者/場地設定"],
                ),
                SurfaceFeature(
                    name="活動營運",
                    description="監控報名漏斗、報到與回饋，並產出 AI 洞察協助調整。",
                    ai_enabled=True,
                    highlights=["報名/出席追蹤", "即時待辦與提醒", "AI 回饋解析"],
                ),
                SurfaceFeature(
                    name="名單管理",
                    description="整合社群與人才檔案，標註徽章並給出下一步行動建議。",
                    ai_enabled=True,
                    highlights=["成員屬性分群", "徽章與歷程", "AI 後續行動建議"],
                ),
                SurfaceFeature(
                    name="成效分析",
                    description="匯總活動轉換、滿意度與媒合成果，提供預測與匯出。",
                    ai_enabled=True,
                    highlights=["ROI/轉換率儀表", "滿意度追蹤", "AI 趨勢預測"],
                ),
            ],
        ),
    )
    return service


if __name__ == "__main__":  # pragma: no cover - manual exploration helper
    svc = bootstrap_demo_service()
    for event in svc.list_events():
        print(f"{event.name} ({event.mode}) - {event.start_at:%Y-%m-%d %H:%M %Z}")
