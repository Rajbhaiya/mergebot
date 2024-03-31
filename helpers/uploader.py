import os
import subprocess
import asyncio
import time

from __init__ import LOGGER
from bot import LOGCHANNEL, userBot
from config import Config
from pyrogram import Client
from pyrogram.types import CallbackQuery, Message

from helpers.display_progress import Progress

async def uploadVideo(
    c: Client,
    cb: CallbackQuery,
    merged_video_path,
    width,
    height,
    duration,
    video_thumbnail,
    file_size,
    upload_mode: bool,
):
    # Split video based on Config.IS_PREMIUM
    max_size = 3.95 * 1024 * 1024 * 1024 if Config.IS_PREMIUM else 1.95 * 1024 * 1024 * 1024
    if os.path.getsize(merged_video_path) > max_size:
        parts = split_video(merged_video_path, max_size)
        for part_path in parts:
            await upload_part(c, cb, part_path, width, height, duration, video_thumbnail, upload_mode)
    else:
        await upload_part(c, cb, merged_video_path, width, height, duration, video_thumbnail, upload_mode)

async def upload_part(c, cb, part_path, width, height, duration, video_thumbnail, upload_mode):
    if Config.IS_PREMIUM:
        sent_ = None
        prog = Progress(cb.from_user.id, c, cb.message)
        async with userBot:
            if upload_mode is False:
                c_time = time.time()
                sent_: Message = await userBot.send_video(
                    chat_id=int(LOGCHANNEL),
                    video=part_path,
                    height=height,
                    width=width,
                    duration=duration,
                    thumb=video_thumbnail,
                    caption=f"`{part_path.rsplit('/',1)[-1]}`\n\nMerged for: {cb.from_user.mention}",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{part_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            else:
                c_time = time.time()
                sent_: Message = await userBot.send_document(
                    chat_id=int(LOGCHANNEL),
                    document=part_path,
                    thumb=video_thumbnail,
                    caption=f"`{part_path.rsplit('/',1)[-1]}`\n\nMerged for: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{part_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            if sent_ is not None:
                await c.copy_message(
                    chat_id=cb.message.chat.id,
                    from_chat_id=sent_.chat.id,
                    message_id=sent_.id,
                    caption=f"`{part_path.rsplit('/',1)[-1]}`",
                )
                # await sent_.delete()
    else:
        try:
            sent_ = None
            prog = Progress(cb.from_user.id, c, cb.message)
            if upload_mode is False:
                c_time = time.time()
                sent_: Message = await c.send_video(
                    chat_id=cb.message.chat.id,
                    video=part_path,
                    height=height,
                    width=width,
                    duration=duration,
                    thumb=video_thumbnail,
                    caption=f"`{part_path.rsplit('/',1)[-1]}`",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{part_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
            else:
                c_time = time.time()
                sent_: Message = await c.send_document(
                    chat_id=cb.message.chat.id,
                    document=part_path,
                    thumb=video_thumbnail,
                    caption=f"`{part_path.rsplit('/',1)[-1]}`",
                    progress=prog.progress_for_pyrogram,
                    progress_args=(
                        f"Uploading: `{part_path.rsplit('/',1)[-1]}`",
                        c_time,
                    ),
                )
        except Exception as err:
            LOGGER.info(err)
            await cb.message.edit("Failed to upload")
        if sent_ is not None:
            if Config.LOGCHANNEL is not None:
                media = sent_.video or sent_.document
                await sent_.copy(
                    chat_id=int(LOGCHANNEL),
                    caption=f"`{media.file_name}`\n\nMerged for: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                )
                
def split_video(input_file, max_size):
    input_size = os.path.getsize(input_file)
    if input_size <= max_size:
        return [input_file]

    subtitle_file = extract_subtitle(input_file)
    if subtitle_file is None:
        return None

    file_name = os.path.splitext(os.path.basename(input_file))[0]

    # Calculate the number of parts based on the max size
    num_parts = math.ceil(input_size / max_size)

    # Calculate the size of each part (approximately equal)
    part_size = math.ceil(input_size / num_parts)

    # Split the video into parts
    parts = []
    for i in range(num_parts):
        part_file = f"{file_name}_part{i + 1}.mp4"
        start_byte = i * part_size
        cmd = [
            "ffmpeg", "-i", input_file, "-c", "copy",
            "-avoid_negative_ts", "make_zero", "-start_at_zero",
            "-copyts", "-y", "-nostats",
            "-ss", str(start_byte), "-fs", str(part_size),
        ]
        if subtitle_file:
            cmd.extend(["-c:s", "mov_text", "-attach", subtitle_file])
        cmd.append(part_file)

        subprocess.run(cmd)

        parts.append(part_file)

    # Clean up temporary subtitle file
    os.remove(subtitle_file)

    return parts

def extract_subtitle(video_file):
    subtitle_file = f"{video_file}.srt"
    cmd = [
        "ffmpeg", "-i", video_file, "-map", "0:s:0", subtitle_file
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0 or not os.path.exists(subtitle_file):
        return None
    return subtitle_file

async def uploadFiles(
    c: Client,
    cb: CallbackQuery,
    up_path,
    n,
    all
):
    try:
        sent_ = None
        prog = Progress(cb.from_user.id, c, cb.message)
        c_time = time.time()
        sent_: Message = await c.send_document(
            chat_id=cb.message.chat.id,
            document=up_path,
            caption=f"`{up_path.rsplit('/',1)[-1]}`",
            progress=prog.progress_for_pyrogram,
            progress_args=(
                f"Uploading: `{up_path.rsplit('/',1)[-1]}`",
                c_time,
                f"\n**Uploading: {n}/{all}**"
            ),
        )
        if sent_ is not None:
            if Config.LOGCHANNEL is not None:
                media = sent_.video or sent_.document
                await sent_.copy(
                    chat_id=int(LOGCHANNEL),
                    caption=f"`{media.file_name}`\n\nExtracted by: <a href='tg://user?id={cb.from_user.id}'>{cb.from_user.first_name}</a>",
                )
    except:
        1    
    1
