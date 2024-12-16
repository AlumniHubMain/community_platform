from aiogram import types
from aiogram import Router, F
from aiogram.fsm.context import FSMContext

from tg_bot.src.data.lexicon import LEXICON_RU
from tg_bot.src.logging.logging_report import report
from tg_bot.src.logging.middleware import LoggingCommands, LoggingCallbacks


async def exit_button(callback: types.CallbackQuery, state: FSMContext):
    """
    Handler triggered by pressing the exit button.
    """
    # удаляем сообщения с кнопкой вызова
    await callback.message.delete()

    # Resetting the current state of the bot
    await state.clear()


async def unknown_command_onboard(message: types.Message):
    """
    Handler that is triggered by a body that is not a command.
    """
    # deleting the trigger message
    await message.delete()

    # we tell the user that there is no such command
    await message.answer(LEXICON_RU['unknown_command'] % message.text)

    # report for admins
    await report(description=f"Пользователь с ником: {message.from_user.username}\nid: {message.from_user.id}\n"
                             f"набрал несуществующую команду: {message.text}")


async def command_not_onboard(message: types.Message):
    """
    Handler that works on the body if the person is not onboarded.
    """
    # deleting the trigger message
    await message.delete()

    # we tell the user that he must first get on board
    await message.answer(LEXICON_RU['not_finished_onboarding'])

    # report for admins
    await report(description=f"Пользователь с ником: {message.from_user.username}\nid: {message.from_user.id}\n"
                             f"использовал команду: {message.text}, не пройдя онбординг! За что был послан!")


# Initialize and fill in the router of the module level
router: Router = Router()
router.message.middleware(LoggingCommands())
router.callback_query.middleware(LoggingCallbacks())

router.callback_query.register(exit_button, F.data.startswith("exit"))
router.message.register(command_not_onboard, F.body, F.chat.type == "private")
