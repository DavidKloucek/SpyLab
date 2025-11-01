import datetime
import re
from collections.abc import Sequence

import numpy as np
from pgvector.sqlalchemy import VECTOR  # type: ignore
from sqlalchemy import cast, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from wireup import service

from app.face_region import FaceRegion
from app.helpers import MetricType, ModelType


@service(lifetime="scoped")
class FaceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_faces_by_image_name(self, fn: str) -> Sequence[FaceRegion]:
        return (await self._session.execute(select(FaceRegion).where(FaceRegion.filename.ilike(fn)))).scalars().all()

    async def find_random(self, limit: int, search: str) -> Sequence[FaceRegion]:
        or_list = []
        for term in re.split(r"\s+", search):
            or_list.append(FaceRegion.filename.ilike(f"%{term}%"))
            or_list.append(FaceRegion.model.ilike(f"%{term}%"))

        q = select(FaceRegion).filter(or_(*or_list)).order_by(func.random()).limit(limit)
        result = await self._session.execute(q)
        return result.scalars().all()

    async def find_all_filenames(self) -> list[str]:
        result = await self._session.execute(select(FaceRegion.filename).group_by(FaceRegion.filename))
        return [str(filename) for filename in result.scalars().all()]

    async def count_regions(self, since: datetime.datetime | None = None) -> int:
        stmt = select(func.count()).select_from(FaceRegion)

        if since is not None:
            stmt = stmt.where(FaceRegion.created_at >= since)

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def find_face_by_id(self, id: int) -> FaceRegion | None:
        q = select(FaceRegion).filter(FaceRegion.id == id)
        result = await self._session.execute(q)
        return result.scalars().first()

    async def get_face_by_id(self, user_id: int) -> FaceRegion:
        res = await self.find_face_by_id(user_id)
        if res is not None:
            return res
        raise FaceRepositoryException()

    async def find_similar_faces(
        self,
        target_vector: np.ndarray,
        model: ModelType,
        metric: MetricType,
        limit: int = 10,
    ) -> list[tuple[FaceRegion, float]]:
        if model == "VGG-Face":
            vector_column = FaceRegion.emb_4096
        elif model == "Facenet":
            vector_column = FaceRegion.emb_128
        elif model in ("ArcFace", "Facenet512"):
            vector_column = FaceRegion.emb_512
        else:
            raise ValueError(f"Model '{model}' is not supported.")

        if metric == "l2":
            distance_func = func.l2_distance
        elif metric == "cosine":
            distance_func = func.cosine_distance
        else:
            raise ValueError(f"Metric '{metric}' is not supported.")

        if not isinstance(target_vector, np.ndarray):
            target_vector = np.array(target_vector)

        target_vector_db = cast(target_vector.tolist(), VECTOR())

        query = (
            select(
                FaceRegion,
                distance_func(vector_column, target_vector_db).label("distance"),
            )
            .filter(FaceRegion.model == model)
            .order_by("distance")
            .limit(limit)
        )

        result = await self._session.execute(query)
        rows = result.all()

        return [(row[0], row.distance) for row in rows]


class FaceRepositoryException(Exception):
    pass
