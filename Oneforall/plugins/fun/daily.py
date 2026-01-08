import random
import asyncio
import time

from pyrogram import filters
from Oneforall import app
from Oneforall.mongo import db

# ────────────────────────────
# Economy DB
# ────────────────────────────
ECONOMY_COLL = db.roshni_economy
PROTECT_COLL = db.roshni_protect


# ────────────────────────────
# /daily
# ────────────────────────────
@app.on_message(filters.command("daily"))
async def daily_cmd(client, message):
    user_id = message.from_user.id

    # Premium check (keep your own logic here)
    is_premium = False

    try:
        user_data = await ECONOMY_COLL.find_one({"user_id": user_id}) or {}
        last_daily = user_data.get("last_daily", 0)
        balance = user_data.get("balance", 0)

        current_time = time.time()
        if current_time - last_daily < 86400:
            remaining = 86400 - (current_time - last_daily)
            hours = int(remaining // 3600)
            mins = int((remaining % 3600) // 60)
            return await message.reply(
                f"⏳ **ʟᴏᴠᴇ, ᴄᴏᴍᴇ ʙᴀᴄᴋ ɪɴ `{hours}ʜ {mins}ᴍ`**"
            )

        amount = 2000 if is_premium else 1000
        new_balance = balance + amount

        await ECONOMY_COLL.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "user_id": user_id,
                    "balance": new_balance,
                    "last_daily": current_time
                }
            },
            upsert=True
        )

        await message.reply(
            "🎀 **ʀᴏsʜɴɪ’ꜱ ᴅᴀɪʟʏ ʙʟᴇssɪɴɢ**\n\n"
            f"💰 sʜᴇ sᴍɪʟᴇᴅ ᴜᴘᴏɴ ʏᴏᴜ · `+${amount:,}`\n"
            f"💳 ɴᴇᴡ ʙᴀʟᴀɴᴄᴇ · `${new_balance:,}`\n\n"
            "✿ _sᴘᴇɴᴅ ɪᴛ ᴡɪsᴇʟʏ, sᴡᴇᴇᴛʜᴇᴀʀᴛ_"
        )

    except Exception:
        await message.reply(
            "❌ **ᴏᴏᴘs… ʀᴏsʜɴɪ sᴛᴜᴍʙʟᴇᴅ ᴀ ʟɪᴛᴛʟᴇ**\n"
            "_ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ sᴏᴏɴ_"
        )


# ────────────────────────────
# /bal
# ────────────────────────────
@app.on_message(filters.command(["bal", "balance"]))
async def bal_cmd(client, message):
    user_id = message.from_user.id

    user_data = await ECONOMY_COLL.find_one({"user_id": user_id}) or {}
    balance = user_data.get("balance", 0)
    last_daily = user_data.get("last_daily", 0)

    hours_ago = int((time.time() - last_daily) // 3600) if last_daily else "ɴᴇᴠᴇʀ"

    text = (
        "୨୧ **ʀᴏsʜɴɪ’ꜱ ᴡᴀʟʟᴇᴛ** ୨୧\n\n"
        f"✦ ᴜsᴇʀ · {message.from_user.mention}\n"
        f"✦ ʙᴀʟᴀɴᴄᴇ · `${balance:,}`\n"
        f"✦ ʟᴀsᴛ ᴅᴀɪʟʏ · `{hours_ago}ʜ ᴀɢᴏ`\n\n"
        "✿ _ʀᴏsʜɴɪ ᴡᴀᴛᴄʜᴇs ᴏᴠᴇʀ ʏᴏᴜʀ ᴄᴏɪɴs_"
    )

    await message.reply(text)
