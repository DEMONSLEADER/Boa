import os

from pyrogram import filters
from pyrogram.types import CallbackQuery
from pyrogram.types import InlineKeyboardButton as IKB
from pyrogram.types import InlineKeyboardMarkup as IKM
from pyrogram.types import Message

from Powers import (LOGGER, RMBG, Audd, genius_lyrics, is_audd,
                    is_genius_lyrics, is_rmbg)
from Powers.bot_class import Gojo
from Powers.utils.custom_filters import command
from Powers.utils.http_helper import post
from Powers.utils.web_helpers import *


@Gojo.on_message(command(["telegraph","tgh","tgm"]))
async def telegraph_upload(c:Gojo,m:Message):
    if not m.reply_to_message:
        await m.reply_text("Reply to media/text to upload it to telegraph")
        return
    file = m.reply_to_message
    if file.text:
        if len(m.command) == 1:
            name = file.from_user.first_name + file.text.split()[1]
        elif len(m.command) > 1:
            name = " ".join(m.command[1:5])
        try:
            upload = telegraph_up(file,name)
        except Exception as e:
            await m.reply_text(f"Got an error\n{e}")
            return
        if upload:
            kb = IKM([[IKB("Here is link to file",url=upload)]])
            await m.reply_text("Here is your uploaded file",disable_web_page_preview=True,reply_markup=kb)
            return
        elif not upload:
            await m.reply_text("Failed to upload the text to telegraph")
            return     
    size = await get_file_size(m.reply_to_message)
    form = size.split(None,1)
    if (form[-1] == "mb" and int(form[0]) > 5) or form[-1] == "gb":
        await m.reply_text("File size too big to upload\nLimit: 5mbs")
        return
    try:
        upload = telegraph_up(file)
    except Exception as e:
        await m.reply_text(f"Got an error\n{e}")
        return
    if upload:
        kb = IKM([[IKB("Here is link to the file",url=upload)]])
        await m.reply_text(f"Here is your file link\n`{upload}`",reply_markup=kb)
        return
    elif not upload:
        await m.reply_text("Failed to upload the file to telegraph")
        return

@Gojo.on_command(command["songname","insong","songinfo","whichsong","rsong","reversesong"])
async def get_song_info(c: Gojo, m: Message):
    if not is_audd:
        await m.reply_text("Audd api is missing add it to use this command")
        return
    reply = m.reply_to_message
    if not reply:
        await m.reply_text("Reply to a video or audio file")
        return
    elif not (reply.video or reply.audio or reply.video_note or (reply.document.mime_type.split("/")[0] in ["video","audio"])):
        await m.reply_text("Reply to a video or audio file")
        return
    URL = "https://api.audd.io/"
    sizee = (await get_file_size(reply)).split()
    if (int(sizee[0]) <= 15 and sizee[1] == "mb") or sizee[1] == "kb":
        fpath = await reply.download()
        files = {
            "file" : open(fpath,"rb")
        }
        BASE_AUDD = {
            "api_token":Audd,
            "return": "spotify"
        }
        result = post(URL,data=BASE_AUDD, files=files)
    elif int(sizee[0]) > 15 or int(sizee[0]) <= 30 and sizee[1] == "mb":
        BASE_AUDD = {
            "api_token":Audd,
            "url": f'{reply.link}',
            "return": "spotify"
        }
        result = post(URL,data=BASE_AUDD)
    else:
        await m.reply_text("File size too big\nI can only fetch file of size upto 30 mbs for now")
        return
    os.remove(fpath)
    if result.status_code != 200:
        await m.reply_text(f"{result.status_code}:{result.text}")
        return
    data = result["result"]
    Artist = data["artist"]
    Title = data["title"]
    Release_date = data["release_date"]
    web_slink = data["song_link"]
    SPOTIFY = data["spotify"]
    spotify_url = SPOTIFY["external_urls"]
    album_url = SPOTIFY["album"]["external_urls"]
    Album = SPOTIFY["album"]["name"]
    photo = SPOTIFY["images"][0]["url"]
    artist_url = SPOTIFY["artists"]["external_urls"]
    cap = f"""
Song name: {Title} 
Artist: {Artist}
Album: {Album}
Release data: {Release_date}
"""
    kb = [
        [
            IKB("🗂 Album", url=album_url),
            IKB("🎨 Artist",url=artist_url)
        ],
        [
            IKB("🎵 Spotify song link",url=spotify_url),
            IKB("♾ More links", url=web_slink)
        ]
    ]
    if is_genius_lyrics:
        g_k = [IKB("📝 Lyrics",f"lyrics_{Artist}:{Title}")]
        kb.append(g_k)

    await m.reply_photo(photo,caption=cap,reply_markup=IKM(kb))
    

@Gojo.on_callback_query(filters.regex("^lyrics_"))
async def lyrics_for_song(c: Gojo, q: CallbackQuery):
    data = q.data.split("_")[1].split(":")
    song = data[1]
    artist = data[0]
    song = genius_lyrics.search_song(song,artist)
    if not song.lyrics:
        await q.answer("‼️ No lyrics found ‼️",True)
        return
    header = f"{song.capitalize()} by {artist}"
    if song.lyrics:
        await q.answer("Fetching lyrics")
        reply = song.lyrics.split("\n",1)[1]
    if len(reply) >= 4096:
        link = telegraph_up(name=header,content=reply)
        cap = "Lyrics was too long\nUploaded it to telegraph"
        new_kb = [
            [
                IKB("Telegraph",url=link)
            ],
            [
                IKB("Close","f_close")
            ]
        ]
    else:
        cap = f"{header}\n{reply}"
        new_kb = [
            [
                IKB("Close","f_close")
            ]
        ]
    await q.message.reply_to_message.reply_text(cap,reply_markup=new_kb)
    await q.message.delete()
    return

@Gojo.on_message(command["removebackground","removebg","rmbg"])
async def remove_background(c: Gojo, m: Message):
    if not is_rmbg:
        await m.reply_text("Add rmbg api to use this command")
        return
    
    reply = m.reply_to_message
    if not reply:
        await m.reply_text("Reply to image to remove it's background")
        return
    elif not (reply.photo or reply.document.mime_type.split("/")[0] == "image" or reply.sticker and (reply.sticker.is_animated or reply.sticker.is_video)):
        await m.reply_text("Reply to image to remove it's background")
        return
    URL = "https://api.remove.bg/v1.0/removebg"
    file = await reply.download("Gojo_Satoru.png")
    to_path = file.replace("\\","/").rsplit("/",1)[0]
    finfo = {'image_file':open(file,'rb')}
    Data = {'size':'auto'}
    Headers = {'X-Api-Key':RMBG}
    result = post(URL,files=finfo,data=Data,headers=Headers)
    os.remove(file)
    if result.status_code != 200:
        await m.reply_text(f"{result.status_code}:{result.text}")
        return
    to_path = f'{to_path}/no-bg.png'
    with open(to_path,'wb') as out:
        out.write(result.content)
    await m.reply_photo(to_path)
    os.remove(to_path)
    return

@Gojo.on_message(command(["song","yta"]))
async def song_down_up(c: Gojo, m: Message):
    splited = m.text.split(None,1)[1].strip()
    if splited.startswith("https://youtube.com"):
        is_direct = True
        query = splited
    else:
        is_direct = False
        query = splited
    try:
        await youtube_downloader(c,m,query,is_direct,"a")
        return
    except Exception as e:
        await m.reply_text(f"Got an error\n{e}")
        return

@Gojo.on_message(command(["vsong","ytv"]))
async def video_down_up(c: Gojo, m: Message):
    splited = m.text.split(None,1)[1].strip()
    if splited.startswith("https://youtube.com"):
        is_direct = True
        query = splited
    else:
        is_direct = False
        query = splited
    try:
        await youtube_downloader(c,m,query,is_direct,"v")
        return
    except Exception as e:
        await m.reply_text(f"Got an error\n{e}")
        return

__PLUGIN__ = "web support"

__HELP__ = """
**Available commands**
• /telegraph (/tgh, /tgm) <page name> : Reply to media which you want to upload to telegraph.
• /rmbg (/removebg, /removebackground) : Reply to image file or sticker of which you want to remove background
• /whichsong (/songname, /songinfo, /insong, /rsong, /reversesong) : Reply to file to get the song playing in it.
• /song (/yta) <songname or youtube link>
• /vsong (/ytv) <songname or youtube link>

**Bot will not download any song or video having duration greater than 5 minutes (to reduce the load on bot's server)**
"""