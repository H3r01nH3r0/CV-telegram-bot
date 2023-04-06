from asyncio import sleep
from pprint import pprint
from typing import Dict

import keyboards
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from PIL import Image, ImageFilter
import pytesseract

bot = Bot(token="5642416515:AAE8iXT8el6KukDAI2F4ciaqUAFb33_7Vpw", parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=MemoryStorage())

messages_for_work = dict()
user_index = dict()


class UserData(StatesGroup):
    data = State()


class CRM(StatesGroup):
    price = State()


async def count_views(user_id: int) -> Dict:
    values = dict()  # Dict with count of views for each public
    views_count = 0  # Summary count of views

    index = user_index[user_id]  # Get index from dict
    content = messages_for_work[user_id]  # Get users dict with messages to check

    for item in content.values():  # For every message in dict download picture and analyze numbers
        # Downloading file
        if index > len(item["items"]):
            continue
        file_id = item["items"][index - 1].photo[-1].file_id
        await bot.download_file_by_id(file_id, destination=f"{user_id}_image.jpg")

        # Open Image, using PIL
        image = Image.open(f"{user_id}_image.jpg")
        image = image.crop((70, 330, 200, 400))
        image = image.filter(ImageFilter.SHARPEN)

        # Read text from picture, using pyTesseract
        # pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        text = pytesseract.image_to_string(image, config='--psm 6 -c tessedit_char_whitelist=0123456789,T')

        # Replacing superfluous dots and commas
        value = text.rstrip().strip(",.").replace(",", ".")

        # Reduction of values to a common
        if "T" in value:
            value = value.replace("T", "")
            value = float(value)
            value = value * 1000
        value = int(value) / 1000
        views_count += value

        values[item["caption"]] = value
    return views_count, values


@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await bot.send_message(
        message.from_user.id,
        text="Hello, choose action",
        reply_markup=keyboards.start()
    )


@dp.message_handler(content_types="text")
async def text_handler(message: types.Message):
    if message.text == "Send pictures!":
        await UserData.data.set()
        await bot.send_message(
            message.from_user.id,
            text="I am waiting for pictures!",
            reply_markup=keyboards.upload_pictures()
        )


@dp.callback_query_handler(state="*")
async def callback_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(
        callback_query.from_user.id,
        callback_query.message.message_id
    )
    if callback_query.data.startswith("story_index"):
        index = int(callback_query.data.split("=")[-1])
        user_index[callback_query.from_user.id] = index
        await CRM.price.set()
        await bot.send_message(
            callback_query.from_user.id,
            text="Enter CRM value.",
            reply_markup=keyboards.cancel()
        )

    elif callback_query.data == "cancel":
        await state.finish()
        del messages_for_work[callback_query.from_user.id]
        await bot.send_message(
            callback_query.from_user.id,
            text="Main menu.",
            reply_markup=keyboards.start()
        )

    elif callback_query.data == "close":
        stories_count = 0
        for key, value in messages_for_work[callback_query.from_user.id].items():
            if stories_count < len(value["items"]):
                stories_count = len(value["items"])
        await bot.send_message(
            callback_query.from_user.id,
            text="Great! What story you ask me to analyze",
            reply_markup=keyboards.from_list_len(stories_count)
        )


@dp.message_handler(content_types=types.ContentType.all(), state=UserData.data)
async def data_handler(message: types.Message, state: FSMContext):
    if message.text == "I have sent all pictures":
        try:
            async with state.proxy() as data:
                messages = data["messages"]
            await state.finish()
            media_groups = set([item.media_group_id for item in messages])
            messages_for_work[message.from_user.id] = dict()
            for media_group_id in media_groups:
                messages_for_work[message.from_user.id][media_group_id] = dict()
                messages_for_work[message.from_user.id][media_group_id]["items"] = sorted(
                    [item for item in messages if item.media_group_id == media_group_id],
                    key=lambda x: x.message_id
                )
                for item in messages_for_work[message.from_user.id][media_group_id]["items"]:
                    if item.caption:
                        messages_for_work[message.from_user.id][media_group_id]["caption"] = item.caption
                        break
                    else:
                        continue
            stories_count = 0
            for key, value in messages_for_work[message.from_user.id].items():
                if stories_count < len(value["items"]):
                    stories_count = len(value["items"])
            await bot.send_message(
                message.from_user.id,
                text="Great! What story you ask me to analyze",
                reply_markup=keyboards.from_list_len(stories_count)
            )
        except KeyError:
            await bot.send_message(
                message.from_user.id,
                text="I haven't received a photo yet"
            )

    elif message.text == "Cancel":
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            text="Canceled.",
            reply_markup=keyboards.start()
        )

    elif message.text == "/start":
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            text="Hello, choose action",
            reply_markup=keyboards.start()
        )

    else:
        async with state.proxy() as data:
            try:
                data["messages"].append(message)
            except KeyError:
                data["messages"] = list()
                data["messages"].append(message)


@dp.message_handler(content_types=types.ContentType.all(), state=CRM.price)
async def crm_handler(message: types.Message, state: FSMContext):
    if message.text == "/start":
        await state.finish()
        await bot.send_message(
            message.from_user.id,
            text="Hello, choose action",
            reply_markup=keyboards.start()
        )
        return
    try:
        crm_value = int(message.text)
    except ValueError:
        await bot.send_message(
            message.from_user.id,
            text="CRM value must be integer!",
            reply_markup=keyboards.cancel()
        )
        return
    summary_views, views_dict = await count_views(message.from_user.id)
    text = f"Summary count of views: {int(summary_views * 1000)}\n"
    sub_views = round(summary_views, 1)
    if sub_views > summary_views:
        sub_views -= 0.1
    summary_price = sub_views * crm_value
    for public_name, views_count in views_dict.items():
        text += "\n"
        new_views_count = round(views_count, 1)
        if new_views_count > views_count:
            new_views_count -= 0.1
        price = new_views_count * crm_value
        text += 'Public: "%s" --> %s views\nPrice: %.1f\n' % (public_name, int(views_count * 1000), price)
    text += "\nSummary price: %.1f" % summary_price
    await state.finish()
    await bot.send_message(
        message.from_user.id,
        text=text,
        reply_markup=keyboards.close()
    )

if __name__ == "__main__":
    executor.start_polling(dispatcher=dp, skip_updates=False)