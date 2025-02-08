from aiogram import F, Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated

from .crud_manager import LoggingManager
from .schemas import DTOUpdateBlockedStatus


async def user_blocked_bot(event: ChatMemberUpdated):
    """
        The handler that triggers the user to ban the bot.
        """

    await LoggingManager.update_blocked_status(DTOUpdateBlockedStatus(telegram_id=event.from_user.id,
                                                                      is_blocked=True))


async def user_unblocked_bot(event: ChatMemberUpdated):
    """
        The handler that triggers the user to unban the bot.
        """

    await LoggingManager.update_blocked_status(DTOUpdateBlockedStatus(telegram_id=event.from_user.id,
                                                                      is_blocked=False))


# Initialize and fill in the router of the module level
router = Router()
router.my_chat_member.filter(F.chat.type == "private")

router.my_chat_member.register(user_blocked_bot, ChatMemberUpdatedFilter(member_status_changed=KICKED))
router.my_chat_member.register(user_unblocked_bot, ChatMemberUpdatedFilter(member_status_changed=MEMBER))
