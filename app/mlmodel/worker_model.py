import asyncio
import json
import logging
import torch
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg
from nats.js.api import StreamConfig, ConsumerConfig
from nats.js.client import JetStreamContext
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import pickle

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] #%(levelname)-8s %(filename)s:%(lineno)d - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

nats_url = "nats://localhost:4222"
model_path = "./distilbert/checkpoint-426363"
mlb_path = "./distilbert/mlb/mlb.pkl"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

model.eval()

with open(mlb_path, "rb") as f:
    mlb = pickle.load(f)


async def message_handler(msg: Msg):
    bucket_name = "my_bucket"

    data = json.loads(msg.data.decode())

    title = data["title"]
    summary = data["summary"]
    request_id = data["request_id"]

    # Подготовка текста
    if title and summary:
        full_text = title + " " + summary
    elif title:
        full_text = title
    else:
        full_text = summary

    inputs = tokenizer(
        full_text,
        padding="max_length",
        truncation=True,
        max_length=512,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.sigmoid(logits).numpy()[0]

    predicted_labels = sorted([[cls, str(prob)] for cls, prob in zip(mlb.classes_, probs)], key=lambda x: float(x[1]), reverse=True)

    result = {"classes": predicted_labels}
    
    try:
        js: JetStreamContext = msg._client.jetstream()
        kv = await js.create_key_value(bucket_name=bucket_name)
    except:
        js: JetStreamContext = msg._client.jetstream()
        kv = await js.key_value(bucket=bucket_name)

    await kv.put(request_id, json.dumps(result).encode())
    await msg.ack()


async def main():
    nc = NATS()
    await nc.connect(nats_url)
    js: JetStreamContext = nc.jetstream()

    stream = StreamConfig(
        name="CLASSIFY",
        subjects=["classification.requests"],
        retention="limits",
        storage="file",
    )
    try:
        await js.add_stream(stream)
    except Exception:
        pass

    consumer_cfg = ConsumerConfig(
        durable_name="worker1",
        ack_policy="explicit"
    )
    await js.subscribe(
        subject="classification.requests",
        cb=message_handler,
        durable=consumer_cfg.durable_name,
        manual_ack=True
    )
    logger.info("The worker is running and listens to messages via JetStream...")
    while True:
        await asyncio.sleep(1)


asyncio.run(main())