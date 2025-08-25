import wireup
from app import dashboard_service, db, face_repository, face_service, image_feeder

container = wireup.create_async_container(
    parameters={},
    service_modules=[
        face_repository,
        face_service,
        dashboard_service,
        image_feeder,
        db,
    ]
)
