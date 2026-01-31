from pyrogram import Client, filters
from pyrogram.types import Message

WELCOME_TEXT = """
⸻⬫⸺〈💖 𝐖ᴇʟᴄᴏᴍᴇ 𝐓ᴏ {group} 💖〉⸺⬫⸻

╭─────────༺✨༻────────╮
 🌸 ➻ 𝐍ᴀᴍᴇ        » {name}
 🆔 ➻ 𝐈ᴅ          » {id}
 🔖 ➻ 𝐔ꜱᴇʀɴᴀᴍᴇ   » {username}
 👥 ➻ 𝐓ᴏᴛᴀʟ 𝐌ᴇᴍʙᴇʀ𝐬 » {members}
╰─────────༺✨༻────────╯

🎉💫 𝐘ᴀʏ! 𝐘ᴏᴜ’ʀᴇ 𝐍ᴏᴡ 𝐏ᴀʀᴛ 𝐎ғ 𝐎ᴜʀ 𝐅ᴀᴍɪʟʏ 💫🎉
💗✨ 𝐄ɴᴊᴏʏ 𝐓ʜᴇ 𝐕ɪʙᴇ𝐬 • 𝐅ᴇᴇʟ 𝐓ʜᴇ 𝐌ᴜꜱɪᴄ ✨💗
"""

@Client.on_message(filters.new_chat_members)
async def welcome_new_member(client: Client, message: Message):
    chat = message.chat
    group_name = chat.title or "This Group"

    try:
        members_count = await client.get_chat_members_count(chat.id)
    except:
        members_count = "—"

    for user in message.new_chat_members:
        name = user.first_name or "Unknown"
        user_id = user.id
        username = f"@{user.username}" if user.username else "None"

        text = WELCOME_TEXT.format(
            group=group_name,
            name=name,
            id=user_id,
            username=username,
            members=members_count
        )

        await message.reply_text(
            text,
            disable_web_page_preview=True
      )
