import hashlib
import tempfile
from typing import Annotated

import numpy as np
from fastapi import UploadFile
from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt
from pydantic.types import PositiveInt
from wireup import Inject, service

from app.app_config import (
    IMG_ORIG_DIR,
    IMG_TEMP_DIR,
    METRIC_DEFAULT,
    MODEL_DEFAULT,
)
from app.face_model_invoker import FaceModelInterface
from app.face_region import FaceRegion
from app.face_repository import FaceRepository
from app.helpers import str_to_metric_type, str_to_model_type
from app.image_processor import crop_and_save


class FaceItem(BaseModel):
    id: PositiveInt
    fn: str
    model: str
    confidence: NonNegativeInt
    preview_path: str
    source_filepath: str
    x: NonNegativeInt
    y: NonNegativeInt
    w: NonNegativeInt
    h: NonNegativeInt


class FaceSimilarItem(FaceItem):
    is_same: bool
    distance: NonNegativeFloat
    quality: NonNegativeFloat


class AnalyzeBox(BaseModel):
    x: NonNegativeInt
    y: NonNegativeInt
    w: NonNegativeInt
    h: NonNegativeInt
    face_confidence: NonNegativeFloat
    similar_faces: NonNegativeInt


@service(lifetime="scoped")
class FaceService:
    def __init__(
        self,
        face_repository: FaceRepository,
        face_engine: FaceModelInterface,
        model_thresholds: Annotated[dict[str, float], Inject(param="model_thresholds")],
    ):
        self._face_repository = face_repository
        self._face_engine = face_engine
        self._model_thresholds = model_thresholds

    def map_face_region_to_item(self, face: FaceRegion) -> FaceItem:
        return FaceItem(
            id=face.id,
            fn=face.filename,
            confidence=round(face.face_confidence * 100),
            model=face.model,
            preview_path=self.create_preview(face),
            source_filepath=face.filename,
            x=face.x,
            y=face.y,
            w=face.w,
            h=face.h,
        )

    async def find_list(self, limit: int, search: str) -> list[FaceItem]:
        return [self.map_face_region_to_item(item) for item in await self._face_repository.find_random(limit, search)]

    def create_preview(self, face: FaceRegion) -> str:
        new_fn = hashlib.sha1(face.filename.encode()).hexdigest() + f"{face.x}_{face.y}_{face.w}_{face.h}.jpg"

        crop_and_save(
            image_path=str(IMG_ORIG_DIR / face.filename),
            x=face.x,
            y=face.y,
            w=face.w,
            h=face.h,
            output_path=str(IMG_TEMP_DIR / new_fn),
            overwrite=False,
        )

        return new_fn

    async def get_photo_faces_by_filename(self, fn: str) -> list[FaceItem]:
        return [self.map_face_region_to_item(x) for x in await self._face_repository.find_faces_by_image_name(fn)]

    async def get_by_id(self, id: int) -> FaceItem:
        return self.map_face_region_to_item(await self._face_repository.get_face_by_id(id))

    async def analyze_image(self, file: UploadFile) -> list[AnalyzeBox]:
        output: list[AnalyzeBox] = []

        contents = await file.read()
        # image = Image.open(io.BytesIO(contents), formats=None).convert("RGB")
        # img_array = np.array(image)
        # faces_data = self.represent_face(img_path=img_array)
        # TODO
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
            faces_data = self._face_engine.represent_face(img_path=tmp_path)

        for data in faces_data:
            emb = data.embedding
            similar_faces = await self.find_similar_by_vector(
                target_vector=np.array(emb),
                model=str_to_model_type(MODEL_DEFAULT),
                metric=str_to_metric_type(METRIC_DEFAULT),
                offset=0,
                limit=100,
                quality=1,
            )
            similar_faces = [item for item in similar_faces if item.distance <= self._model_thresholds[MODEL_DEFAULT]]

            output.append(
                AnalyzeBox(
                    x=data.facial_area.x,
                    y=data.facial_area.y,
                    w=data.facial_area.w,
                    h=data.facial_area.h,
                    face_confidence=data.face_confidence,
                    similar_faces=len(similar_faces),
                )
            )

        return output

    async def find_similar_by_image(
        self, file: UploadFile, x: int, y: int, w: int, h: int, limit: int, offset: int, quality: int | None
    ) -> list[FaceSimilarItem]:
        contents = await file.read()
        # image = Image.open(io.BytesIO(contents)).convert("RGB")
        # img_array = np.array(image)
        # cropped_array = img_array[y:y+h, x:x+w, :]
        # faces_data = self.represent_face(img_path=img_array)
        # TODO
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
            faces_data = self._face_engine.represent_face(img_path=tmp_path)

        vector = None
        for data in faces_data:
            area = data.facial_area
            if area.x == x and area.y == y and area.w == w and area.h == h:
                vector = data.embedding
                break

        if vector is None:
            raise ValueError("Vector not found")

        return await self.find_similar_by_vector(
            target_vector=np.array(vector),
            model=MODEL_DEFAULT,
            metric=METRIC_DEFAULT,
            quality=quality,
            limit=limit,
            offset=offset,
        )

    async def find_similar_by_face_id(
        self, id: int, model: str, metric: str, limit: int, quality: int | None
    ) -> list[FaceSimilarItem]:
        face_row = await self._face_repository.get_face_by_id(id)
        target_vector = face_row.get_vector()
        return await self.find_similar_by_vector(
            target_vector=target_vector, model=model, metric=metric, limit=limit, quality=quality, offset=0
        )

    async def find_similar_by_vector(
        self, target_vector: np.ndarray, model: str, metric: str, limit: int, offset: int, quality: int | None
    ) -> list[FaceSimilarItem]:
        similar_faces = await self._face_repository.find_similar_faces(
            target_vector=target_vector,
            model=str_to_model_type(model),
            metric=str_to_metric_type(metric),
            limit=limit,
            quality=quality,
        )

        resp: list[FaceSimilarItem] = []

        for face, distance in similar_faces:
            new_fn = self.create_preview(face)

            resp.append(
                FaceSimilarItem(
                    id=face.id,
                    fn=face.filename,
                    confidence=round(face.face_confidence * 100),
                    distance=distance,
                    quality=face.face_quality,
                    model=face.model,
                    preview_path=new_fn,
                    source_filepath=face.filename,
                    is_same=self._model_thresholds[face.model] >= distance,
                    x=face.x,
                    y=face.y,
                    w=face.w,
                    h=face.h,
                )
            )

        return resp
