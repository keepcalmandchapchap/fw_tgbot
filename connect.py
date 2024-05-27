from sqlalchemy import create_engine
from telebot import TeleBot

def connect_db():
    driver = '' # драйвер базы данных
    user = '' # имя пользователя
    password = '' # пароль
    connect = '' # соединение
    port = '' # порт
    database = '' # название БД
    DSN = f'{driver}://{user}:{password}@{connect}:{port}/{database}'
    engine = create_engine(DSN)
    return engine


def connect_bot():
    TOKEN = '' # токен, полученный у BotFather
    return TeleBot(TOKEN)