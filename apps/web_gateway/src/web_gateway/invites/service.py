import logging
import string
import secrets
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from common_db.models import ORMInviteCode


logger = logging.get_logger(__name__)
MAX_TRIES = 100


class InvitesManager:
    @staticmethod
    async def generate_code():
        alphabet = string.ascii_letters + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(8))

    @staticmethod
    async def get_user_by_invite_code(session: AsyncSession, code: str) -> int | None:
        res = await session.execute(select(ORMInviteCode).where(ORMInviteCode.code == code, ORMInviteCode.active))
        user = res.scalar_one_or_none()
        return user

    @staticmethod
    async def get_invite_code(session: AsyncSession, user_id: int) -> str | None:
        res = await session.execute(select(ORMInviteCode).where(ORMInviteCode.user_id == user_id, active=True))
        user = res.scalar_one_or_none()
        return user

    @staticmethod
    async def create_new_ref_code(session: AsyncSession, user_id: int) -> str:
        await session.execute(update(ORMInviteCode).where(ORMInviteCode.user_id == user_id).values(active=False))

        for _ in range(MAX_TRIES):
            new_code = await InvitesManager.generate_code()
            try:
                invite_code = ORMInviteCode(user_id=user_id, code=new_code, active=True)
                session.add(invite_code)
                await session.commit()
                return new_code
            except Exception as e:
                await session.rollback()
                logger.warning("Code collision: %s", str(e))

        raise RuntimeError("Max tries exceeded for creating a unique invite code")
