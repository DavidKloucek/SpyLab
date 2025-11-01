from __future__ import annotations

from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, NonNegativeInt
from wireup import service

from app.face_service import FaceRepository
from app.user_repository import UserRepository


@service(lifetime="scoped")
class DashboardService:
    def __init__(self, face_repository: FaceRepository, user_repository: UserRepository):
        self._face_repository = face_repository
        self._user_repository = user_repository

    async def get_stats(self) -> DashStats:
        return DashStats(
            face_count_total=await self._face_repository.count_regions(),
            face_count_24h=await self._face_repository.count_regions(since=datetime.now(UTC) - timedelta(hours=24)),
            user_count_total=await self._user_repository.count_all(),
        )


class DashStats(BaseModel):
    face_count_total: NonNegativeInt
    face_count_24h: NonNegativeInt
    user_count_total: NonNegativeInt
