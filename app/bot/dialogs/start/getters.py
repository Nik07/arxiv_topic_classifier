from aiogram.types import User
from aiogram_dialog import DialogManager
from fluentogram import TranslatorRunner


async def get_send_title(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> dict[str, str]:

    return {
        "send_title": i18n.send.title(),
        "no_title": i18n.no.title(),
    }


async def get_send_summary(
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
    **kwargs,
) -> dict[str, str]:

    return {
        "send_summary": i18n.send.summary(),
        "no_summary": i18n.no.summary(),
        "is_title": dialog_manager.dialog_data.get('title') is not None
    }