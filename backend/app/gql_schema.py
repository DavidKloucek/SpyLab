
import strawberry
from strawberry.fastapi import BaseContext

from app.container import container
from app.dashboard_service import DashboardService


class DIContext(BaseContext):
    def __init__(self, scoped):
        self._scoped = scoped

    async def get[T](self, cls: type[T]) -> T:
        return await self._scoped.get(cls)


async def get_context():
    async with container.enter_scope() as scoped:
        return DIContext(scoped)


@strawberry.type
class HelloItem:
    id: int

    @strawberry.field
    async def hello_item(self, info: strawberry.Info[DIContext, None]) -> str:
        ds = await info.context.get(DashboardService)
        print(id(ds))
        return f"DashboardService ID: {id(ds)}"


@strawberry.type
class Query:
    @strawberry.field
    async def hello(self, info: strawberry.Info[DIContext, None]) -> str:
        ds = await info.context.get(DashboardService)
        ds2 = await info.context.get(DashboardService)
        s = await ds.get_stats()
        return f"Count: {s.face_count_total}, service ID: {id(ds)}, {id(ds2)}"

    @strawberry.field
    async def hello_list(self, info: strawberry.Info[DIContext, None]) -> list[HelloItem]:
        ds = await info.context.get(DashboardService)
        print(id(ds))
        return [HelloItem(id=1), HelloItem(id=2)]


schema = strawberry.Schema(query=Query)
