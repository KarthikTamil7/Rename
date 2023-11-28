from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply

from hachoir.metadata import extractMetadata
from hachoir.parser import createParser

from helper.utils import progress_for_pyrogram, convert, humanbytes
from helper.database import db
from pyrogram.emoji import *
from asyncio import sleep
from PIL import Image
import os, time

@Client.on_message(filters.command("mode") & filters.private & filters.incoming)
async def set_mode(c, m):
    upload_mode = await db.get_upload_mode(m.from_user.id)
    if upload_mode:
        await update_mode(m.from_user.id, False)
        text = f"**From Now all files will be Uploaded as Video {VIDEO_CAMERA}**"
    else:
        await update_mode(m.from_user.id, True)
        text = f"**From Now all files will be Uploaded as Files {FILE_FOLDER}**"
    await m.reply_text(text, quote=True)

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    mention = message.from_user.mention
    if file.file_size > 2000 * 1024 * 1024:
         await message.reply_text("**Sorry {mention} This Bot is Doesn't Support Uploading Files Bigger Than 2GB. So you Can Use 4GB Rename Bot 👉🏻 [4GB Rename Star Bots](https://t.me/Star_4GB_Rename_Bot)**")

    try:
        await message.reply_text(
            text=f"**__Please Enter New File Name...__\n\nOld File Name :-** `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )       
        await sleep(30)
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**__Please Enter New File Name...__\n\nOld File Name :-** `{filename}`",
	    reply_to_message_id=message.id,  
	    reply_markup=ForceReply(True)
        )
        await uploader(message)

async def uploader(bot, update):
    new_name = update.message.text
    new_filename = new_name.split(":-")[1]
    file_path = f"downloads/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("**Trying to 📥 Downloading...**")    
    try:
     	path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram,progress_args=("**📥 Download Started...**", ms, time.time()))                    
    except Exception as e:
     	return await ms.edit(e)
     	     
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata.has("duration"):
           duration = metadata.get('duration').seconds
    except:
        pass
    ph_path = None
    user_id = int(update.message.chat.id) 
    media = getattr(file, file.media.value)
    upload_as_doc = await db.get_upload_as_doc(update.message.chat.id)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
         try:
             caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
         except Exception as e:
             return await ms.edit(text=f"**Your Caption Error Except Keyword Argument ({e})**")             
    else:
         caption = f"**{new_filename}**"
 
    if (media.thumbs or c_thumb):
         if c_thumb:
             ph_path = await bot.download_media(c_thumb) 
         else:
             ph_path = await bot.download_media(media.thumbs[0].file_id)
         Image.open(ph_path).convert("RGB").save(ph_path)
         img = Image.open(ph_path)
         img.resize((320, 320))
         img.save(ph_path, "JPEG")

    await ms.edit("**Trying to 📤 Uploading...**")
    type = message.data.split("_")[1]
    try:
        if (upload_as_doc is True) or (type == "document"):
            await bot.send_document(
                update.message.chat.id,
                document=file_path,
                thumb=ph_path, 
                caption=caption, 
                progress=progress_for_pyrogram,
                progress_args=("**📤 Upload Status :-**", ms, time.time()))
        elif (upload_as_doc is False) and (type == "video"): 
            await bot.send_video(
		update.message.chat.id,
	        video=file_path,
	        caption=caption,
		thumb=ph_path,
		duration=duration,
	        progress=progress_for_pyrogram,
		progress_args=("**📤 Upload Status :-**", ms, time.time()))
        elif (upload_as_doc is False) and (type == "audio"):
            await bot.send_audio(
		update.message.chat.id,
		audio=file_path,
		caption=caption,
		thumb=ph_path,
		duration=duration,
	        progress=progress_for_pyrogram,
	        progress_args=("**📤 Upload Status :-**", ms, time.time()))
    except Exception as e:          
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        return await ms.edit(f"**Error :- {e}**")
 
    await ms.delete() 
    os.remove(file_path) 
    if ph_path: os.remove(ph_path) 
