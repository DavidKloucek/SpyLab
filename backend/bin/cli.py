import asyncio
from app.container import container
from app.face_repository import FaceRepository


async def main():
    async with container.enter_scope() as scoped:
        repo = await scoped.get(FaceRepository)
        c = await repo.count_regions()
        print(f"Count: {c}")


if __name__ == "__main__":
    asyncio.run(main())
