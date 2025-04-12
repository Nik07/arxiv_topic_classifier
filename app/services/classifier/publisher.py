import json
import uuid
import asyncio

from aiogram import Bot
from aiogram.enums.chat_action import ChatAction
from fluentogram import TranslatorRunner
from nats.aio.client import Client as NATS
from nats.js.client import JetStreamContext


async def classify(
    nc: NATS, js: JetStreamContext, bot: Bot, i18n: TranslatorRunner, chat_id: int, subject: str, title: str = '', summary: str = ''
) -> None:
    if len(title) + len(summary) <=25:
        await bot.send_message(chat_id=chat_id, text=i18n.impossible.classify())
        return

    bucket_name = "my_bucket"

    request_id = str(uuid.uuid4())
    
    message = {
        "request_id": request_id,
        "title": title,
        "summary": summary,
    }

    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        kv = await js.create_key_value(bucket=bucket_name)
    except:
        kv = await js.key_value(bucket=bucket_name)
        
    try:
        await js.publish(subject, json.dumps(message).encode())

        watcher = await kv.watch(keys=request_id)
        update = await watcher.updates()

        if update is None:
            update = await watcher.updates(timeout=10)

        classes = json.loads(update.value.decode()).get('classes')

        top_classes = []
        cum_sum = 0
        for cls in classes:
            cum_sum += float(cls[1])
            top_classes.append(cls)
            if cum_sum >= 0.95:
                break

        output = f"{i18n.top.topics()}\n\n" \
                 f'{"\n".join([f'<b>{cls[0]}</b>: {float(cls[1]):.3f}' for cls in top_classes])}\n\n' \
                 f"{i18n.new.classification()}" 

        await bot.send_message(chat_id=chat_id, text=output)
        return
    except asyncio.TimeoutError:
        return "Ошибка: время ожидания ответа истекло."
    except Exception as e:
        return f"Ошибка: {str(e)}"
