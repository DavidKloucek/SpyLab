from typing import Awaitable, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from app.face_repository import FaceRepository
from app.face_service import FaceService
import os
from app.face_region import FaceRegion
from app.app_config import IMG_ORIG_DIR
from wireup import service


@service(lifetime="scoped")
class ImageFeeder:
    def __init__(
        self,
        face_repository: FaceRepository,
        face_service: FaceService,
        session: AsyncSession,
    ):
        self._face_repo = face_repository
        self._face_service = face_service
        self._session = session

    async def process(self, progress_cb: Callable[[str], Awaitable[None]] | None = None):
        async def send_msg(s: str):
            if progress_cb:
                await progress_cb(s)

        models = [
            # 'Facenet',
            # 'Facenet512',
            # 'VGG-Face',
            "ArcFace"
        ]

        success_img_count = 0

        all_fns_db = await self._face_repo.find_all_filenames()

        new_files = []
        for f in os.listdir(IMG_ORIG_DIR):
            if (
                f not in all_fns_db
                and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
                and os.path.isfile(os.path.join(IMG_ORIG_DIR, f))
            ):
                new_files.append(f)

        for fn in new_files:
            print(f"Processing {fn}")

            for model in models:
                try:
                    faces_data = self._face_service.represent_face(img_path=IMG_ORIG_DIR / fn)

                    for data in faces_data:
                        quality = 0.0
                        if (
                            data["facial_area"]["w"] >= 30
                            and data["facial_area"]["h"] >= 30
                            and data["face_confidence"] >= 0.6
                        ):
                            quality = 1.0

                        face = FaceRegion(
                            filename=fn,
                            face_confidence=data["face_confidence"],
                            face_quality=quality,
                            x=data["facial_area"]["x"],
                            y=data["facial_area"]["y"],
                            w=data["facial_area"]["w"],
                            h=data["facial_area"]["h"],
                            left_eye=list(map(int, data["facial_area"]["left_eye"])),
                            right_eye=list(map(int, data["facial_area"]["right_eye"])),
                            model=model,
                            vector=data["embedding"],
                        )
                        self._session.add(face)
                        await self._session.commit()
                    print(f"Done: {model}")

                except ValueError:
                    print(f"Error: {model}")

            await self._session.commit()

            success_img_count += 1

        print(f"Processed images: {success_img_count}")
