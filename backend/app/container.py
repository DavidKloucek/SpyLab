import wireup

from app import app_config as cfg
from app import (
    auth_service,
    dashboard_service,
    db,
    face_model_invoker,
    face_repository,
    face_service,
    image_feeder,
    user_repository,
)

container = wireup.create_async_container(
    parameters={
        "model_thresholds": cfg.MODEL_THRESHOLDS,
        "model_name": cfg.MODEL_DEFAULT,
        "detector_backend": cfg.DETECTOR_BACKEND,
    },
    service_modules=[
        face_repository,
        face_service,
        dashboard_service,
        user_repository,
        image_feeder,
        auth_service,
        face_model_invoker,
        db,
    ],
)
