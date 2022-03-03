import os
import ffmpeg
import logging
from io import BytesIO
from uuid import uuid4
from pytube import YouTube
from telegram import (
    Update,
    InputMediaAudio,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultVideo,
    InputTextMessageContent,
    InlineQueryResultCachedAudio,
)
from telegram.ext import (
    Updater,
    CallbackContext,
    InlineQueryHandler,
    CallbackQueryHandler,
)
from youtubesearchpython import VideosSearch

API_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)


def InlineQuery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    if query == "":
        return
    if any(
        string in query
        for string in [
            "https://music.youtube.com/",
            "https://www.youtube.com/",
            "https://youtu.be/",
        ]
    ):
        link = query.replace(
            "https://www.youtube.com/watch?v=", "https://youtu.be/")
        audio = url(link, True)
        message = context.bot.send_audio(
            chat_id=5170164823,
            audio=audio["audio"],
            duration=audio["length"],
            title=audio["title"],
            filename=audio["title"],
            performer=audio["artist"],
            timeout=(5 * 60),
        )
        update.inline_query.answer(
            [
                InlineQueryResultCachedAudio(
                    id=str(uuid4()),
                    audio_file_id=message.audio.file_id,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Use FFmpeg (Better audio)", callback_data=query
                                )
                            ],
                            [
                                InlineKeyboardButton(
                                    "Naah I'm good", callback_data="End"
                                )
                            ],
                        ]
                    ),
                )
            ]
        )

    else:
        results = []
        videos = VideosSearch(query, limit=15).result()["result"]
        for video in videos:
            title = video["title"]
            link = video["link"]
            try:
                description = video["descriptionSnippet"][0]["text"]
            except:
                description = "No description"
            duration = video["duration"]
            thumbnail = video["thumbnails"][0]["url"]
            results.append(
                InlineQueryResultVideo(
                    id=str(uuid4()),
                    video_url=link,
                    mime_type="video/mp4",
                    thumb_url=thumbnail,
                    title=title,
                    description=f"Duration:{duration}\n{description}",
                    input_message_content=InputTextMessageContent(link),
                )
            )
        update.inline_query.answer(results)


def Callback(update: Update, context: CallbackContext) -> None:
    update.callback_query.answer()
    if update.callback_query.data == "End":
        context.bot.edit_message_reply_markup(
            inline_message_id=update.callback_query.inline_message_id,
            reply_markup=InlineKeyboardMarkup([]),
        )
    else:
        link = update.callback_query.data.replace(
            "https://www.youtube.com/watch?v=", "https://youtu.be/"
        )
        audio = url(link, False)
        message = context.bot.send_audio(
            chat_id=5170164823,
            audio=audio["audio"],
            duration=audio["length"],
            title=audio["title"],
            filename=audio["title"],
            performer=audio["artist"],
            timeout=(5 * 60),
        )
        context.bot.edit_message_media(
            inline_message_id=update.callback_query.inline_message_id,
            media=InputMediaAudio(media=message.audio.file_id),
        )


def url(link, type: bool):
    yt = YouTube(link)
    if type:
        buffer = BytesIO()
        yt.streams.get_audio_only().stream_to_buffer(buffer)
        buffer.seek(0)
        mp3 = buffer
    else:
        mp3, _ = (
            ffmpeg.input(yt.streams.get_audio_only().url)
            .output("pipe:", format="mp3", acodec="libmp3lame")
            .run(capture_stdout=True)
        )
    audio = {
        "audio": mp3,
        "title": yt.title,
        "length": yt.length,
        "artist": yt.author.replace(" - Topic", ""),
    }
    return audio


def main() -> None:
    updater = Updater(API_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(InlineQueryHandler(InlineQuery))
    dispatcher.add_handler(CallbackQueryHandler(Callback))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
