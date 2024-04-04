import os
import subprocess
import asyncio
import time
import math

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
            duration = 1
            try:
                metadata = extractMetadata(createParser(part_path))
                if metadata.has("duration"):
                    duration = metadata.get("duration").seconds
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
    os.remove(part_path)
                
def split_video(video_path, max_size_bytes):
    """
    Split a video into multiple parts of equal size, including the subtitle track, with each part being less than the specified maximum size (in bytes).

    Args:
        video_path (str): The path to the input video file.
        max_size_bytes (int): The maximum size (in bytes) for each split video part.

    Returns:
        list: A list of paths to the split video parts.
    """
    video_size_bytes = os.path.getsize(video_path)

    # Calculate the number of parts needed
    num_parts = math.ceil(video_size_bytes / max_size_bytes)

    # Get the video duration
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    duration = float(probe.stdout.strip())

    # Calculate the duration of each part
    part_duration = duration / num_parts

    parts = []
    for i in range(num_parts):
        start_time = i * part_duration
        end_time = min((i + 1) * part_duration, duration)

        # Generate the output filename
        part_filename = f"part_{i+1}.mp4"

        # Split the video using FFmpeg and copy existing subtitles
        subprocess.run(["ffmpeg", "-i", video_path, "-ss", str(start_time), "-t", str(end_time - start_time), "-c", "copy", "-c:s", "mov_text", "-map", "0", "-map", "0:s?", part_filename])

        parts.append(part_filename)

    return parts

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
