
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from wireup import service

from app.user import User


class UserNotFoundException(BaseException):
    pass


@service(lifetime="scoped")
class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def count_all(self) -> int:
        stmt = select(func.count()).select_from(User)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def find_all(self, offset: int, limit: int) -> list[User]:
        stmt = select(User).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def find_by_email(self, email: str) -> User | None:
        q = select(User).filter(User.email == email)
        result = await self._session.execute(q)
        return result.scalars().first()

    async def find_by_id(self, id: int) -> User | None:
        q = select(User).filter(User.id == id)
        result = await self._session.execute(q)
        return result.scalars().first()

    async def get_by_id(self, id: int) -> User:
        res = await self.find_by_id(id)
        if res is not None:
            return res
        raise UserNotFoundException()
