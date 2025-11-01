import mimetypes
from abc import ABC, abstractmethod
from typing import Annotated, override

import httpx
from deepface import DeepFace  # type: ignore
from pydantic import BaseModel, Field, NonNegativeFloat, NonNegativeInt
from wireup import Inject, abstract, service


class FacialArea(BaseModel):
    x: NonNegativeInt
    y: NonNegativeInt
    w: NonNegativeInt
    h: NonNegativeInt
    left_eye: tuple[NonNegativeInt, NonNegativeInt]
    right_eye: tuple[NonNegativeInt, NonNegativeInt]


class FaceEmbedding(BaseModel):
    embedding: Annotated[list[float], Field(min_length=1)]
    facial_area: FacialArea
    face_confidence: NonNegativeFloat


class FaceEmbeddingList(BaseModel):
    faces: list[FaceEmbedding]

    def __iter__(self):
        return iter(self.faces)

    @property
    def count(self):
        return len(self.faces)


@abstract
class FaceModelInterface(ABC):
    @abstractmethod
    def represent_face(self, img_path: str) -> FaceEmbeddingList: ...


class NoFaceFound(Exception):
    pass


class RemoteFaceModel(FaceModelInterface):
    def __init__(
        self,
        detector_backend: Annotated[str, Inject(param="detector_backend")],
        model_name: Annotated[str, Inject(param="model_name")],
    ):
        self._detector_backend = detector_backend
        self._model_name = model_name

    @override
    def represent_face(self, img_path: str) -> FaceEmbeddingList:
        """TODO"""
        url = "http://localhost:8002/api/represent"
        form_data = {
            "detector_backend": self._detector_backend,
            "model_name": self._model_name,
        }
        with open(img_path, "rb") as image_file:
            mime_type, _ = mimetypes.guess_type(img_path)
            files = {"file": (img_path, image_file, mime_type or "application/octet-stream")}
            resp = httpx.post(url, data=form_data, files=files)
            data = FaceEmbeddingList.model_validate({"faces": resp.json()})
            return data


@service(lifetime="scoped")
class LocalFaceModel(FaceModelInterface):
    def __init__(
        self,
        detector_backend: Annotated[str, Inject(param="detector_backend")],
        model_name: Annotated[str, Inject(param="model_name")],
    ):
        self._detector_backend = detector_backend
        self._model_name = model_name

    @override
    def represent_face(self, img_path: str) -> FaceEmbeddingList:
        try:
            data = DeepFace.represent(
                img_path=img_path,
                model_name=self._model_name,
                detector_backend=self._detector_backend,
            )
            validated = FaceEmbeddingList.model_validate({"faces": data})
            return validated
        except ValueError as e:
            if e.args and str(e.args[0]).startswith("Face could not be detected"):
                raise NoFaceFound(str(e.args[0]))
            raise e
