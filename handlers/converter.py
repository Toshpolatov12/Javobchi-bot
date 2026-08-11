import os
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from bot.database import log_file_activity, get_user_lang
from bot.locales import MESSAGES
from keyboards.converter_kb import get_format_keyboard, build_format_descriptions_text
from utils.file_helper import get_extension, cleanup, generate_output_path
from converters.registry import get_available_formats, get_converter, get_file_category
from bot.config import MAX_FILE_SIZE
from bot.main import bot

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.document)
async def document_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    doc = message.document

    if not doc.file_name:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await message.answer(MESSAGES[lang]["too_large"])
        return

    ext = get_extension(doc.file_name)
    if not ext:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    formats = get_available_formats(ext)
    if not formats:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    category = get_file_category(ext)
    category_emoji = {
        "image": "🖼", "document": "📄", "spreadsheet": "📊",
        "archive": "📦", "data": "💾", "ebook": "📚", "video": "🎥"
    }.get(category, "📁")

    descriptions_text = build_format_descriptions_text(formats, lang)

    info_text = (
        f"{category_emoji} <b>{doc.file_name}</b>\n"
        f"📏 {doc.file_size / (1024 * 1024):.1f} MB | 🏷 {ext.upper()}\n\n"
        f"<b>{MESSAGES[lang]['select_format']}</b>\n\n"
        f"{descriptions_text}"
    )

    await message.answer(
        info_text,
        parse_mode="HTML",
        reply_to_message_id=message.message_id,
        reply_markup=get_format_keyboard(formats, lang)
    )


@router.message(F.photo)
async def photo_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    photo = message.photo[-1]

    if photo.file_size and photo.file_size > MAX_FILE_SIZE:
        await message.answer(MESSAGES[lang]["too_large"])
        return

    formats = get_available_formats("jpg")
    if not formats:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    descriptions_text = build_format_descriptions_text(formats, lang)

    info_text = (
        f"🖼 <b>Rasm / Image</b>\n"
        f"📏 {photo.file_size / 1024:.1f} KB | 🏷 JPG\n\n"
        f"<b>{MESSAGES[lang]['select_format']}</b>\n\n"
        f"{descriptions_text}"
    )

    await message.answer(
        info_text,
        parse_mode="HTML",
        reply_to_message_id=message.message_id,
        reply_markup=get_format_keyboard(formats, lang)
    )


@router.message(F.video)
async def video_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    video = message.video

    if video.file_size and video.file_size > MAX_FILE_SIZE:
        await message.answer(MESSAGES[lang]["too_large"])
        return

    file_name = video.file_name or "video.mp4"
    ext = get_extension(file_name) or "mp4"

    formats = get_available_formats(ext)
    if not formats:
        formats = get_available_formats("mp4")

    if not formats:
        await message.answer(MESSAGES[lang]["unsupported"])
        return

    descriptions_text = build_format_descriptions_text(formats, lang)

    info_text = (
        f"🎥 <b>Video: {file_name}</b>\n"
        f"📏 {video.file_size / (1024 * 1024):.1f} MB | 🏷 {ext.upper()}\n\n"
        f"<b>{MESSAGES[lang]['select_format']}</b>\n\n"
        f"{descriptions_text}"
    )

    await message.answer(
        info_text,
        parse_mode="HTML",
        reply_to_message_id=message.message_id,
        reply_markup=get_format_keyboard(formats, lang)
    )


@router.callback_query(F.data.startswith("cvt:"))
async def convert_callback(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    target_ext = call.data.split(":")[1]

    # Get original message with the file
    orig_msg = call.message.reply_to_message
    if not orig_msg:
        await call.message.edit_text(MESSAGES[lang]["error"] + "\n\n⚠️ Original message not found.")
        await call.answer()
        return

    # Extract file info from original message
    if orig_msg.document:
        file_id = orig_msg.document.file_id
        file_name = orig_msg.document.file_name or "file"
        file_size = orig_msg.document.file_size or 0
        source_ext = get_extension(file_name)
    elif orig_msg.photo:
        photo = orig_msg.photo[-1]
        file_id = photo.file_id
        file_name = "photo.jpg"
        file_size = photo.file_size or 0
        source_ext = "jpg"
    elif orig_msg.video:
        video = orig_msg.video
        file_id = video.file_id
        file_name = video.file_name or "video.mp4"
        file_size = video.file_size or 0
        source_ext = get_extension(file_name) or "mp4"
    else:
        await call.message.edit_text(MESSAGES[lang]["error"])
        await call.answer()
        return

    # Get converter
    converter_fn = get_converter(source_ext, target_ext)
    if not converter_fn:
        await call.message.edit_text(MESSAGES[lang]["unsupported"])
        await call.answer()
        return

    # Show progress
    await call.message.edit_text(MESSAGES[lang]["converting"])

    input_path = None
    output_path = None

    try:
        # Download file from Telegram
        file = await bot.get_file(file_id)
        input_path = f"/tmp/{file_name}"
        await bot.download_file(file.file_path, input_path)

        # Generate output path
        output_path = generate_output_path(file_name, target_ext)

        # Run conversion
        result_path = await converter_fn(input_path, output_path)

        # Read result and send back
        with open(result_path, "rb") as f:
            result_data = f.read()

        output_name = os.path.basename(result_path)
        result_file = BufferedInputFile(result_data, filename=output_name)

        # Send based on output type
        if target_ext == "gif":
            # Send as Telegram GIF / Animation
            await call.message.answer_animation(result_file)
        elif target_ext == "ogg":
            # Send as Telegram Voice Note
            await call.message.answer_voice(result_file)
        elif target_ext in ["mp3", "wav", "m4a"]:
            # Send as Telegram Audio Track
            await call.message.answer_audio(result_file)
        else:
            # Send as Document
            await call.message.answer_document(result_file)

        await call.message.edit_text(MESSAGES[lang]["done"])

        # Log to database
        await log_file_activity(
            user_id=call.from_user.id,
            file_name=file_name,
            file_type=source_ext,
            file_size=file_size,
            action=f"{source_ext}→{target_ext}",
            target_format=target_ext,
            status="success"
        )

    except ValueError as ve:
        if str(ve) == "gif_too_long":
            await call.message.edit_text(MESSAGES[lang]["gif_too_long"])
        else:
            await call.message.edit_text(MESSAGES[lang]["error"])
    except Exception as e:
        logger.error(f"Conversion error {source_ext}->{target_ext}: {e}")
        await call.message.edit_text(
            MESSAGES[lang]["error"] + f"\n\n<code>{type(e).__name__}</code>",
            parse_mode="HTML"
        )
        await log_file_activity(
            user_id=call.from_user.id,
            file_name=file_name,
            file_type=source_ext,
            file_size=file_size,
            action=f"{source_ext}→{target_ext}",
            target_format=target_ext,
            status=f"error: {str(e)[:100]}"
        )
    finally:
        cleanup(input_path, output_path)

    await call.answer()


@router.callback_query(F.data == "cancel_cvt")
async def cancel_conversion(call: CallbackQuery):
    lang = await get_user_lang(call.from_user.id)
    await call.message.edit_text("❌ " + MESSAGES[lang]["cancel"])
    await call.answer()
