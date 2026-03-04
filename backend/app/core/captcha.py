import uuid, base64, random, string
from io import BytesIO
from captcha.image import ImageCaptcha
import redis.asyncio as aioredis

image_captcha = ImageCaptcha(width=200, height=70, font_sizes=(38, 42, 46))
CAPTCHA_TTL = 300

def _random_text(length: int = 5) -> str:
    chars = string.ascii_uppercase.replace("O","").replace("I","") + string.digits.replace("0","")
    return "".join(random.choices(chars, k=length))

async def generate_captcha(redis_client: aioredis.Redis) -> dict:
    captcha_id = str(uuid.uuid4())
    text = _random_text()
    data = image_captcha.generate(text)
    b64 = base64.b64encode(data.read()).decode("utf-8")
    await redis_client.setex(f"captcha:{captcha_id}", CAPTCHA_TTL, text)
    return {"captcha_id": captcha_id, "image_base64": f"data:image/png;base64,{b64}"}

async def verify_captcha(redis_client: aioredis.Redis, captcha_id: str, answer: str) -> bool:
    key = f"captcha:{captcha_id}"
    stored = await redis_client.get(key)
    if not stored:
        return False
    await redis_client.delete(key)
    return stored.decode().upper() == answer.strip().upper()
