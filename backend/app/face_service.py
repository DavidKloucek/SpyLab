from wireup import service
import hashlib
import tempfile
from typing import List
from fastapi import UploadFile
from pydantic import BaseModel
from pydantic.types import PositiveInt
from app.face_region import FaceRegion
from app.app_config import (
    DETECTOR_BACKEND,
    IMG_ORIG_DIR,
    IMG_TEMP_DIR,
    METRIC_DEFAULT,
    MODEL_DEFAULT,
    MODEL_THRESHOLDS,
)
from app.image_processor import crop_and_save
from app.face_repository import FaceRepository
from app.helpers import str_to_metric_type, str_to_model_type
from deepface import DeepFace  # type: ignore
import numpy as np


class FaceItem(BaseModel):
    id: PositiveInt
    fn: str
    model: str
    confidence: float
    preview_path: str
    source_filepath: str
    x: int
    y: int
    w: int
    h: int


class FaceSimilarItem(FaceItem):
    is_same: bool
    distance: float
    quality: float


class AnalyzeBox(BaseModel):
    x: int
    y: int
    w: int
    h: int
    face_confidence: float
    similar_faces: int


class NoFaceFound(Exception):
    pass


@service(lifetime="scoped")
class FaceService:
    _face_repository: FaceRepository

    def __init__(self, face_repository: FaceRepository):
        self._face_repository = face_repository

    def represent_face(self, img_path):
        try:
            return DeepFace.represent(
                img_path=img_path,
                model_name=MODEL_DEFAULT,
                detector_backend=DETECTOR_BACKEND,
            )
        except ValueError as e:
            if e.args and str(e.args[0]).startswith("Face could not be detected"):
                raise NoFaceFound(str(e.args[0]))
            raise e

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

    async def find_list(self, limit: int, search: str) -> List[FaceItem]:
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

    async def get_photo_faces_by_filename(self, fn: str) -> List[FaceItem]:
        return [self.map_face_region_to_item(x) for x in await self._face_repository.find_faces_by_image_name(fn)]

    async def get_by_id(self, id: int) -> FaceItem:
        return self.map_face_region_to_item(await self._face_repository.get_face_by_id(id))

    async def analyze_image(self, file: UploadFile) -> List[AnalyzeBox]:
        output: List[AnalyzeBox] = []

        contents = await file.read()
        # image = Image.open(io.BytesIO(contents), formats=None).convert("RGB")
        # img_array = np.array(image)
        # faces_data = self.represent_face(img_path=img_array)
        # TODO
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
            faces_data = self.represent_face(img_path=tmp_path)

        for data in faces_data:
            emb = data["embedding"]
            similar_faces = await self.find_similar_by_vector(
                target_vector=emb,
                model=str_to_model_type(MODEL_DEFAULT),
                metric=str_to_metric_type(METRIC_DEFAULT),
                limit=100,
            )
            similar_faces = [item for item in similar_faces if item.distance <= MODEL_THRESHOLDS[MODEL_DEFAULT]]

            output.append(
                AnalyzeBox(
                    x=data["facial_area"]["x"],
                    y=data["facial_area"]["y"],
                    w=data["facial_area"]["w"],
                    h=data["facial_area"]["h"],
                    face_confidence=data["face_confidence"],
                    similar_faces=len(similar_faces),
                )
            )

        return output

    async def find_similar_by_image(
        self, file: UploadFile, x: int, y: int, w: int, h: int, limit: int
    ) -> List[FaceSimilarItem]:
        contents = await file.read()
        # image = Image.open(io.BytesIO(contents)).convert("RGB")
        # img_array = np.array(image)
        ## cropped_array = img_array[y:y+h, x:x+w, :]
        # faces_data = self.represent_face(img_path=img_array)
        # TODO
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=True) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
            faces_data = self.represent_face(img_path=tmp_path)

        vector = None
        for data in faces_data:
            area = data["facial_area"]
            if area["x"] == x and area["y"] == y and area["w"] == w and area["h"] == h:
                vector = data["embedding"]
                break

        if vector is None:
            raise ValueError("Vector not found")

        return await self.find_similar_by_vector(
            target_vector=vector,
            model=MODEL_DEFAULT,
            metric=METRIC_DEFAULT,
            limit=limit,
        )

    async def find_similar_by_face_id(self, id: int, model: str, metric: str, limit: int) -> List[FaceSimilarItem]:
        face_row = await self._face_repository.get_face_by_id(id)
        target_vector = face_row.get_vector()
        return await self.find_similar_by_vector(target_vector=target_vector, model=model, metric=metric, limit=limit)

    async def find_similar_by_vector(
        self, target_vector: np.ndarray, model: str, metric: str, limit: int
    ) -> List[FaceSimilarItem]:
        similar_faces = await self._face_repository.find_similar_faces(
            target_vector=target_vector,
            model=str_to_model_type(model),
            metric=str_to_metric_type(metric),
            limit=limit,
        )

        resp: List[FaceSimilarItem] = []

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
                    is_same=MODEL_THRESHOLDS[face.model] >= distance,
                    x=face.x,
                    y=face.y,
                    w=face.w,
                    h=face.h,
                )
            )

        return resp
