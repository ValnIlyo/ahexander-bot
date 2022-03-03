import os
import ffmpeg
import logging
from uuid import uuid4
from pytube import YouTube
from telegram import (
    Update,
    InputMediaAudio,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultVideo,
    InputTextMessageContent,
    InlineQueryResultDocument,
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


def InlineQuery(update: Update, _: CallbackContext) -> None:
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
        update.inline_query.answer(
            [
                InlineQueryResultDocument(
                    id=str(uuid4()),
                    title="It's a promise!",
                    document_url="https://drive.google.com/u/1/uc?id=13KSKdlfSriTitnezyEyJ9jHvkEld4_2F&export=download",
                    mime_type="application/pdf",
                    description="Click me to be able to recieve your audio :)",
                    caption="Looks yummy doesn't it? Uwu",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Get your audio", callback_data=query)]]
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
    if any(
        string in update.callback_query.data
        for string in [
            "https://music.youtube.com/",
            "https://www.youtube.com/",
            "https://youtu.be/",
        ]
    ):
        link = update.callback_query.data.replace(
            "https://www.youtube.com/watch?v=", "https://youtu.be/"
        )
        audio = url(link)
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


def url(link):
    yt = YouTube(link)
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
