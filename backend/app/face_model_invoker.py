from deepface import DeepFace  # type: ignore
from typing import Annotated, List, Tuple
from pydantic import BaseModel, Field, NonNegativeInt, PositiveFloat
from wireup import Inject, service


class FacialArea(BaseModel):
    x: NonNegativeInt
    y: NonNegativeInt
    w: NonNegativeInt
    h: NonNegativeInt
    left_eye: Tuple[PositiveFloat, PositiveFloat]
    right_eye: Tuple[PositiveFloat, PositiveFloat]


class FaceEmbedding(BaseModel):
    embedding: Annotated[List[float], Field(min_length=1)]
    facial_area: FacialArea
    face_confidence: PositiveFloat


class FaceEmbeddingList(BaseModel):
    faces: list[FaceEmbedding]

    def __iter__(self):
        return iter(self.faces)

    @property
    def count(self):
        return len(self.faces)


class NoFaceFound(Exception):
    pass


@service(lifetime="scoped")
class FaceModelInvoker:
    def __init__(
        self,
        detector_backend: Annotated[str, Inject(param="detector_backend")],
        model_name: Annotated[str, Inject(param="model_name")],
    ):
        self._detector_backend = detector_backend
        self._model_name = model_name

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
