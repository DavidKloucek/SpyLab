from pathlib import Path
from decouple import Config, RepositoryEnv  # type: ignore
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

config = Config(RepositoryEnv(os.path.join(BASE_DIR, ".env")))

APP_TITLE = config("APP_TITLE")
DATABASE_URL = config("DATABASE_URL")

IMG_ORIG_DIR = Path(os.path.abspath(os.path.join(BASE_DIR, config("IMG_ORIG_DIR"))))
IMG_TEMP_DIR = Path(os.path.abspath(os.path.join(BASE_DIR, config("IMG_TEMP_DIR"))))

PRIVATE_KEY_PATH = Path(os.path.abspath(os.path.join(BASE_DIR, config("PRIVATE_KEY_PATH"))))
PUBLIC_KEY_PATH = Path(os.path.abspath(os.path.join(BASE_DIR, config("PUBLIC_KEY_PATH"))))

ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES"))
ALGORITHM = str(config("ALGORITHM"))

GQL_PATH = "/graphql"
IMG_TEMP_DIR_URL_PATH = "/preview"
IMG_ORIG_DIR_URL_PATH = "/source_img"

MODEL_DEFAULT = "ArcFace"
METRIC_DEFAULT = "cosine"
DETECTOR_BACKEND = "mtcnn"

MODEL_THRESHOLDS = {
    'Facenet': 0.8,
    'Facenet512': 0.5,
    'VGG-Face': 0.6,
    'ArcFace': 0.6
}
MODEL_VECTOR_SIZES = {
    "VGG-Face": 4096,
    "Facenet": 128,
    "ArcFace": 512,
    "Facenet512": 512
}
ALLOWED_ORIGINS = [
    "http://localhost:4200",
    "http://localhost:9000",
    "http://localhost:3000",
    "http://localhost:5173"
]
