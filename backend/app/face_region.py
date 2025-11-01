from datetime import UTC, datetime

import numpy as np
from pgvector.sqlalchemy import Vector  # type: ignore
from sqlalchemy import JSON, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.app_config import MODEL_VECTOR_SIZES
from app.db import Base


class FaceRegion(Base):
    __tablename__ = "face_region"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(250), nullable=False)
    emb_128: Mapped[np.ndarray | None] = mapped_column(Vector(128), nullable=True)
    emb_512: Mapped[np.ndarray | None] = mapped_column(Vector(512), nullable=True)
    emb_4096: Mapped[np.ndarray | None] = mapped_column(Vector(4096), nullable=True)
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    w: Mapped[int] = mapped_column(Integer)
    h: Mapped[int] = mapped_column(Integer)
    left_eye: Mapped[dict[str, int] | list[int] | None] = mapped_column(JSON)
    right_eye: Mapped[dict[str, int] | list[int] | None] = mapped_column(JSON)
    face_confidence: Mapped[float] = mapped_column(Float)
    face_quality: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(String(25), nullable=False)

    def __init__(
        self,
        filename: str,
        x: int,
        y: int,
        w: int,
        h: int,
        left_eye: dict[str, int] | list[int] | None,
        right_eye: dict[str, int] | list[int] | None,
        face_confidence: float,
        face_quality: float,
        model: str,
        vector: dict[str, float] | np.ndarray,
    ) -> None:
        self.filename = filename
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.left_eye = left_eye
        self.right_eye = right_eye
        self.face_confidence = face_confidence
        self.face_quality = face_quality
        self.created_at = datetime.now(UTC)
        self.model = model
        self.set_vector_by_type(vector, model)

    def set_vector_by_type(self, vector: dict[str, float] | np.ndarray, model: str) -> None:
        if isinstance(vector, dict):
            vector = np.array(list(vector.values()), dtype=np.float32)
        if isinstance(vector, list):
            vector = np.array(vector, dtype=np.float32)
        if not isinstance(vector, np.ndarray):
            raise TypeError(f"Expected np.ndarray, got {type(vector)}")

        expected_size = MODEL_VECTOR_SIZES.get(model)

        if expected_size and vector.shape[0] != expected_size:
            raise ValueError(f"Expected vector of size {expected_size} for model '{model}', got {vector.shape[0]}")

        self.emb_512 = None
        self.emb_128 = None
        self.emb_4096 = None

        if model == "VGG-Face":
            self.emb_4096 = vector
        elif model == "Facenet":
            self.emb_128 = vector
        elif model in ("ArcFace", "Facenet512"):
            self.emb_512 = vector
        else:
            raise ValueError(f"Model '{model}' not implemented yet")

    def get_vector(self) -> np.ndarray:
        def type_ok(v):
            if not isinstance(v, np.ndarray):
                raise TypeError
            return v

        model = self.model
        if model == "VGG-Face":
            return type_ok(self.emb_4096)
        elif model == "Facenet":
            return type_ok(self.emb_128)
        elif model == "ArcFace" or model == "Facenet512":
            return type_ok(self.emb_512)
        else:
            raise Exception(f"Model '{model}' not implemented yet")
