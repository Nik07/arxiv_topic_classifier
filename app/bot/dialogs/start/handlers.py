from aiogram import Bot
from aiogram.types import CallbackQuery, Message
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner
from app.bot.states.start import StartSG
from app.services.classifier.publisher import classify
from nats.aio.client import Client as NATS
from nats.js.client import JetStreamContext


async def no_title_button_click(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await dialog_manager.switch_to(state=StartSG.summary)


async def save_title(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    dialog_manager.dialog_data.update(title=message.text)
    await dialog_manager.switch_to(state=StartSG.summary)


async def no_summary_button_click(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    bot: Bot = dialog_manager.middleware_data.get('bot')
    nc: NATS = dialog_manager.middleware_data.get('nc')
    js: JetStreamContext = dialog_manager.middleware_data.get('js')
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    title = dialog_manager.dialog_data.get('title')
    await dialog_manager.done()
    await classify(nc=nc, js=js, bot=bot, i18n=i18n, chat_id=callback.from_user.id, subject="classification.requests", title=title)


async def save_summary(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    bot: Bot = dialog_manager.middleware_data.get('bot')
    nc: NATS = dialog_manager.middleware_data.get('nc')
    js: JetStreamContext = dialog_manager.middleware_data.get('js')
    i18n: TranslatorRunner = dialog_manager.middleware_data.get('i18n')
    title = dialog_manager.dialog_data.get('title')
    await dialog_manager.done()
    await classify(nc=nc, js=js, bot=bot, i18n=i18n, chat_id=message.from_user.id, subject="classification.requests", title=title if title else '', summary=message.text)