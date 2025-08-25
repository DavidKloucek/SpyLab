from datetime import datetime, timedelta, timezone
from fastapi import Depends
from pydantic import BaseModel
from app.face_service import FaceRepository
from wireup import service


@service(lifetime="scoped")
class DashboardService:
    _repository: FaceRepository

    def __init__(self, face_repository: FaceRepository):
        self._repository = face_repository

    async def get_stats(self) -> "DashStats":
        return DashStats(
            face_count_total=await self._repository.count_regions(),
            face_count_24h=await self._repository.count_regions(
                since=datetime.now(timezone.utc)-timedelta(hours=24)
            ),
        )


class DashStats(BaseModel):
    face_count_total: int
    face_count_24h: int
