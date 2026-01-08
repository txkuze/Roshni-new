import time
from pyrogram import filters
from Oneforall import app
from Oneforall.mongo import db

ECONOMY_COLL = db.roshni_economy


@app.on_message(filters.command(["daily"]))
async def daily_cmd(client, message):
    user_id = message.from_user.id
    is_premium = False

    user_data = await ECONOMY_COLL.find_one({"user_id": user_id}) or {}
    last_daily = user_data.get("last_daily", 0)
    balance = user_data.get("balance", 0)

    now = time.time()
    if now - last_daily < 86400:
        left = int((86400 - (now - last_daily)) // 3600)
        return await message.reply_text(
            f"⏳ **ʟᴏᴠᴇ, ᴄᴏᴍᴇ ʙᴀᴄᴋ ɪɴ `{left}ʜ`**"
        )

    amount = 2000 if is_premium else 1000
    new_balance = balance + amount

    await ECONOMY_COLL.update_one(
        {"user_id": user_id},
        {"$set": {
            "user_id": user_id,
            "balance": new_balance,
            "last_daily": now
        }},
        upsert=True
    )

    await message.reply_text(
        f"🎀 **ʀᴏsʜɴɪ’ꜱ ᴅᴀɪʟʏ ʙʟᴇssɪɴɢ**\n\n"
        f"💰 `+${amount:,}`\n"
        f"💳 ʙᴀʟᴀɴᴄᴇ · `${new_balance:,}`"
    )


@app.on_message(filters.command(["bal", "balance"]))
async def bal_cmd(client, message):
    user_id = message.from_user.id
    data = await ECONOMY_COLL.find_one({"user_id": user_id}) or {}

    await message.reply_text(
        f"୨୧ **ʀᴏsʜɴɪ’ꜱ ᴡᴀʟʟᴇᴛ** ୨୧\n\n"
        f"💳 `${data.get('balance', 0):,}`"
    )
