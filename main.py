import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, html 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, URLInputFile, CallbackQuery, ReplyKeyboardRemove
from dotenv import load_dotenv

from utils.commands import FILMS_COMMAND, FILM_CREATE_COMMAND

from data_film.data import get_films, add_film
from keyboards.keyboards import films_keyboard_markup, FilmCallback

from models.models import Film
from utils.states import FilmForm

import logging


load_dotenv()

TOKEN: str = os.getenv("TOKEN")

dp = Dispatcher()

logger = logging.getLogger(__name__)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:

    await message.answer(f"Приветствую, {html.bold(message.from_user.full_name)}!\n"
                         f"Я первый бот Python разработчика - Лія Макарова")


@dp.message(FILMS_COMMAND)
async def command_start_handler(message: Message) -> None:
    data = get_films()
    markup = films_keyboard_markup(films_list=data)

    await message.answer(f"Список фильмов. Нажмите на название чтобы узнать больше", reply_markup=markup)


@dp.message(FILM_CREATE_COMMAND)
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.set_state(FilmForm.name)
    await message.answer(
        text= f'Enter a movie name.',
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(FilmForm.name)
async def film_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f'Enter a movie description', reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.description)


@dp.message(FilmForm.description)
async def film_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(f'Enter a movie rating from zero to ten', reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.rating)


@dp.message(FilmForm.rating)
async def film_rating(message: Message, state: FSMContext) -> None:
    await state.update_data(rating=message.text)
    await message.answer(f'Enter the movie genre', reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.genre)


@dp.message(FilmForm.genre)
async def film_genre(message: Message, state: FSMContext) -> None:
    await state.update_data(genre=message.text)
    await message.answer(
        text=f"Enter the movie actors through a separator ', '\n"
             + html.bold("A comma and an indent after it are required."),
        reply_markup=ReplyKeyboardRemove(),
    )
    await state.set_state(FilmForm.actors)


@dp.message(FilmForm.actors)
async def film_actors(message: Message, state: FSMContext) -> None:
    actors_list = [actor.strip() for actor in message.text.split(',')]

    await state.update_data(actors=actors_list)
    await message.answer(f'Enter a movie poster', reply_markup=ReplyKeyboardRemove())
    await state.set_state(FilmForm.poster)


@dp.message(FilmForm.poster)
async def film_poster(message: Message, state: FSMContext) -> None:
    data = await state.update_data(poster=message.text)
    film = Film(**data)
    add_film(film.model_dump())
    await state.clear()
    await message.answer(f'{film.name} movie successfully added!',
                         reply_markup=ReplyKeyboardRemove())
    

@dp.callback_query(FilmCallback.filter())
async def calb_film(callback: CallbackQuery, callback_data: FilmCallback):
    film_id = callback_data.id
    film_data = get_films(film_id=film_id)
    film = Film(**film_data)

    text = f"Movie: {film.name}\n" \
           f"Description: {film.description}\n" \
           f"Rating: {film.rating}\n" \
           f"Genre: {film.genre}\n" \
           f"Actors: {', '.join(film.actors)}\n"

    await callback.message.answer_photo(
        caption=text,
        photo=URLInputFile(
            film.poster,
            filename=f"{film.name}_poster.{film.poster.split('.')[-1]}"
        )
    )

async def main() -> None:
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    logger.info('Started')
    await dp.start_polling(bot)


if __name__ == "__main__":
    
    asyncio.run(main())
