import asyncio
from app.container import container
from app.image_feeder import ImageFeeder


async def main():
    async with container.enter_scope() as scoped:
        feeder = await scoped.get(ImageFeeder)
        await feeder.process()


if __name__ == "__main__":
    asyncio.run(main())
