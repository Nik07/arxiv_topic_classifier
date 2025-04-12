import gradio as gr
import asyncio
import uuid
import json
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js.client import JetStreamContext

nats_url = "nats://localhost:4222"

nc: NATS | None = None


async def classify_text(title, summary):
    if len(title) + len(summary) < 25:
        return 'Impossible to classify'
    global nc
    if nc is None or not nc.is_connected:
        nc = NATS()
        await nc.connect(nats_url)

    bucket_name = "my_bucket"

    request_id = str(uuid.uuid4())
    
    message = {
        "request_id": request_id,
        "title": title,
        "summary": summary,
    }
    
    try:
        js: JetStreamContext = nc.jetstream()
        kv = await js.create_key_value(bucket=bucket_name)
    except:
        js: JetStreamContext = nc.jetstream()
        kv = await js.key_value(bucket=bucket_name)

    try:
        await nc.publish("classification.requests", json.dumps(message).encode())

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

        output = "\n".join([f'{cls[0]}: {float(cls[1]):.3f}' for cls in top_classes])

        return output
    except asyncio.TimeoutError:
        return "Ошибка: время ожидания ответа истекло."
    except Exception as e:
        return f"Ошибка: {str(e)}"
    finally:
        if nc.is_connected:
            await nc.drain()


def sync_classify_text(text_title, text_summary):
    return asyncio.run(classify_text(text_title, text_summary))


def check_inputs(text_title: str, text_summary: str):
    if text_title and text_title.strip() or text_summary and text_summary.strip():
        return gr.update(interactive=True)
    return gr.update(interactive=False)


with gr.Blocks() as demo:
    gr.HTML("<h1 style='text-align: center;'>Classifier of scientific articles by topic</h1>")
    
    with gr.Row():
        with gr.Column():
            text_title = gr.Textbox(label="Topic", placeholder="Enter the title of the article...")
            text_summary = gr.Textbox(label="Abstract", placeholder="Enter the article's abstract...")
            submit_btn = gr.Button("Classify", interactive=False, variant='primary')
        
        with gr.Column():
            result_text = gr.Textbox(label="Top 95%")
    
    # Проверка ввода для активации кнопки
    text_title.change(fn=check_inputs, inputs=[text_title, text_summary], outputs=submit_btn)
    text_summary.change(fn=check_inputs, inputs=[text_title, text_summary], outputs=submit_btn)
    
    # Обработка нажатия кнопки
    submit_btn.click(
        fn=sync_classify_text,
        inputs=[text_title, text_summary],
        outputs=[result_text]
    )

demo.launch()