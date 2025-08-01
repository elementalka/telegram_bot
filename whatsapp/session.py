import asyncio
from pathlib import Path
from aiogram.types import FSInputFile
import qrcode
import os

WA_DIR = Path("wa_session")

async def create_session(bot, chat_id: int):
    WA_DIR.mkdir(exist_ok=True)
    proc = await asyncio.create_subprocess_exec(
        "node", "wa_login.js", str(WA_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=Path(__file__).resolve().parent.parent
    )

    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        text = line.decode().strip()
        if text.startswith("QR:"):
            qr_data = text[3:]
            img_path = WA_DIR / "qr.png"
            qrcode.make(qr_data).save(img_path)
            await bot.send_photo(chat_id, FSInputFile(img_path), caption="Сканируйте QR для входа в WhatsApp")
        elif text == "READY":
            await bot.send_message(chat_id, "✅ Сессия WhatsApp готова")
            break
        elif text.startswith("AUTH_FAIL:"):
            await bot.send_message(chat_id, f"❌ Ошибка авторизации: {text[10:]}")
            break
    await proc.wait()

async def delete_session():
    if WA_DIR.exists():
        for item in WA_DIR.iterdir():
            if item.is_file():
                item.unlink()
            else:
                import shutil
                shutil.rmtree(item)
        WA_DIR.rmdir()
