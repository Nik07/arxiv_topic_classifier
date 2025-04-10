from aiogram.enums import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput

from app.bot.dialogs.start.getters import get_send_summary, get_send_title
from app.bot.dialogs.start.handlers import no_summary_button_click, no_title_button_click, save_summary, save_title
from app.bot.states.start import StartSG

start_dialog = Dialog(
    Window(
        Format("{send_title}"), 
        Button(
            text=Format("{no_title}"),
            id='no_title_button',
            on_click=no_title_button_click
        ),
        MessageInput(
            func=save_title,
            content_types=ContentType.TEXT
        ),
        getter=get_send_title, 
        state=StartSG.title
    ),
     Window(
        Format("{send_summary}"), 
        Button(
            text=Format("{no_summary}"),
            id='no_summary_button',
            on_click=no_summary_button_click,
            when='is_title'
        ),
        MessageInput(
            func=save_summary,
            content_types=ContentType.TEXT
        ),
        getter=get_send_summary, 
        state=StartSG.summary
    ),
)
