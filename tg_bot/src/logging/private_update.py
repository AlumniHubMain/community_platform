from aiogram import F, Router
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.types import ChatMemberUpdated

from .crud_manager import LoggingManager
from .logging_report import report
from .schemas import DTOUpdateBlockedStatus


async def user_blocked_bot(event: ChatMemberUpdated):
    """
        Хэндлер, срабатывающий на блокирование бота пользователем.
        """
    try:
        await LoggingManager.update_blocked_status(DTOUpdateBlockedStatus(telegram_id=event.from_user.id,
                                                                          is_blocked=True))
    except Exception as e:
        await report(description=f'Ошибка при обновлении статуса блокировки бота\n'
                                 f'username: {event.from_user.username}\nid: {event.from_user.id}\n'
                                 f'is blocked: True\n',
                     extent='error',
                     exception=e)


async def user_unblocked_bot(event: ChatMemberUpdated):
    """
        Хэндлер, срабатывающий на разблокирование бота пользователем.
        """
    try:
        await LoggingManager.update_blocked_status(DTOUpdateBlockedStatus(telegram_id=event.from_user.id,
                                                                          is_blocked=False))
    except Exception as e:
        await report(description=f'Ошибка при обновлении статуса блокировки бота\n'
                                 f'username: {event.from_user.username}\nid: {event.from_user.id}\n'
                                 f'is blocked: False\n',
                     extent='error',
                     exception=e)


# Инициализируем и заполняем роутер уровня модуля
router = Router()
router.my_chat_member.filter(F.chat.type == "private")

router.my_chat_member.register(user_blocked_bot, ChatMemberUpdatedFilter(member_status_changed=KICKED))
router.my_chat_member.register(user_unblocked_bot, ChatMemberUpdatedFilter(member_status_changed=MEMBER))
