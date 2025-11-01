from __future__ import annotations

from enum import Enum
from typing import Literal, TypeVar, cast

import numpy as np

Vector = TypeVar("Vector", bound=list[float])


class ModelType2(Enum):
    VGG_FACE = "VGG-Face"
    FACENET = "Facenet"
    ARCFACE = "ArcFace"
    FACENET512 = "Facenet512"

    @staticmethod
    def from_str(s: str) -> ModelType2:
        try:
            return ModelType2(s)
        except ValueError:
            raise ValueError(f"{s} is not a valid model")


ModelType = Literal["VGG-Face", "Facenet", "ArcFace", "Facenet512"]

MetricType = Literal["l2", "cosine"]


def str_to_model_type(s: str) -> ModelType:
    if s in ["VGG-Face", "Facenet", "ArcFace", "Facenet512"]:
        return cast(ModelType, s)
    raise ValueError(f"{s} is not a valid model")


def str_to_metric_type(s: str) -> MetricType:
    if s in ["l2", "cosine"]:
        return cast(MetricType, s)
    raise ValueError(f"{s} is not a valid metric")


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        return np.array(vector)
    return np.array(vector) / norm


class Embedding:
    def __init__(self, embedding_json: list[float]):
        self.embedding_json = embedding_json


def distance(a: Embedding, b: Embedding) -> float:
    return float(np.linalg.norm(normalize(np.array(a.embedding_json)) - normalize(np.array(b.embedding_json))))
