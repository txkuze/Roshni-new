import random
import time
import asyncio
from pyrogram import filters
from pyrogram.enums import ParseMode
from Oneforall import app
from Oneforall.mongo import db

# Collections
ECONOMY = db.roshni_economy
COOLDOWNS = db.roshni_cooldowns
ITEMS = db.roshni_items

async def get_bal(user_id):
    user = await ECONOMY.find_one({"user_id": user_id})
    return user.get("balance", 0) if user else 0

async def update_bal(user_id, amount):
    await ECONOMY.update_one({"user_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)

# --- ECONOMY COMMANDS ---

@app.on_message(filters.command(["daily", "claim"]))
async def daily_cmd(_, message):
    uid = message.from_user.id
    is_premium = message.from_user.is_premium
    now = time.time()
    
    cd = await COOLDOWNS.find_one({"user_id": uid})
    if cd and now - cd.get("daily", 0) < 86400:
        rem = 86400 - (now - cd["daily"])
        return await message.reply(f"⏳ **Roshni says:** Come back in {int(rem//3600)}h {int((rem%3600)//60)}m!")

    reward = 2000 if is_premium else 1000
    await update_bal(uid, reward)
    await COOLDOWNS.update_one({"user_id": uid}, {"$set": {"daily": now}}, upsert=True)
    await message.reply(f"🎁 **Daily Reward!**
💰 Roshni gave you `${reward:,}`
{'💖 *Premium Bonus Included*' if is_premium else ''}")

@app.on_message(filters.command(["bal", "balance"]))
async def bal_cmd(_, message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    balance = await get_bal(target.id)
    await message.reply(f"💳 **{target.first_name}'s Balance:** `${balance:,}`")

@app.on_message(filters.command("rob"))
async def rob_cmd(_, message):
    if not message.reply_to_message:
        return await message.reply("❌ Reply to someone to rob them!")
    
    robber = message.from_user.id
    victim = message.reply_to_message.from_user.id
    if robber == victim: return

    is_premium = message.from_user.is_premium
    rob_limit = 100000 if is_premium else 10000
    v_bal = await get_bal(victim)

    if v_bal < 500: return await message.reply("Victim is too poor!")

    if random.randint(1, 100) <= (50 if is_premium else 40):
        stolen = min(random.randint(200, int(v_bal * 0.4)), rob_limit)
        await update_bal(robber, stolen)
        await update_bal(victim, -stolen)
        await message.reply(f"🎯 **Success!** Stole `${stolen:,}` from {message.reply_to_message.from_user.first_name}!")
    else:
        fine = 500
        await update_bal(robber, -fine)
        await message.reply(f"👮 **Caught!** You paid `${fine}` fine to Roshni.")

@app.on_message(filters.command("give"))
async def give_cmd(_, message):
    if not message.reply_to_message or len(message.command) < 2:
        return await message.reply("Usage: Reply `/give 500`")
    
    try:
        amount = int(message.command[1])
        if amount <= 0: return
    except: return

    sender_bal = await get_bal(message.from_user.id)
    if sender_bal < amount: return await message.reply("❌ Insufficient funds!")
    
    await update_bal(message.from_user.id, -amount)
    await update_bal(message.reply_to_message.from_user.id, amount)
    await message.reply(f"✅ Transferred `${amount:,}` to {message.reply_to_message.from_user.first_name}.")

# --- GAME COMMANDS ---

@app.on_message(filters.command("kill"))
async def kill_cmd(_, message):
    if not message.reply_to_message: return
    cost = 1000
    bal = await get_bal(message.from_user.id)
    if bal < cost: return await message.reply(f"❌ Killing costs `${cost}`")
    
    await update_bal(message.from_user.id, -cost)
    await ITEMS.update_one({"user_id": message.reply_to_message.from_user.id}, {"$set": {"is_dead": True}}, upsert=True)
    await message.reply(f"💀 {message.reply_to_message.from_user.first_name} was killed by {message.from_user.first_name}!")

@app.on_message(filters.command("revive"))
async def revive_cmd(_, message):
    cost = 2000
    bal = await get_bal(message.from_user.id)
    if bal < cost: return await message.reply(f"❌ Revive costs `${cost}`")
    
    await update_bal(message.from_user.id, -cost)
    await ITEMS.update_one({"user_id": message.from_user.id}, {"$set": {"is_dead": False}}, upsert=True)
    await message.reply(f"😇 Roshni revived {message.from_user.first_name}!")

@app.on_message(filters.command("protect"))
async def protect_cmd(_, message):
    cost = 5000
    bal = await get_bal(message.from_user.id)
    if bal < cost: return await message.reply("❌ Shield costs $5000")
    
    await update_bal(message.from_user.id, -cost)
    await COOLDOWNS.update_one({"user_id": message.from_user.id}, {"$set": {"shield_until": time.time() + 86400}}, upsert=True)
    await message.reply("🛡️ Shield active for 24 hours!")

@app.on_message(filters.command("toprich"))
async def toprich_cmd(_, message):
    top = ECONOMY.find().sort("balance", -1).limit(10)
    text = "👑 **ROSHNI'S RICHEST**

"
    i = 1
    async for user in top:
        text += f"{i}. ID: `{user['user_id']}` — `${user['balance']:,}`
"
        i += 1
    await message.reply(text)
