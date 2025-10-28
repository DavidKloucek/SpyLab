import wireup
from app import (
    auth_service,
    dashboard_service,
    db,
    face_repository,
    face_service,
    image_feeder,
    user_repository,
)

container = wireup.create_async_container(
    parameters={},
    service_modules=[
        face_repository,
        face_service,
        dashboard_service,
        user_repository,
        image_feeder,
        auth_service,
        db,
    ],
)
