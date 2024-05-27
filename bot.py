import random 
import time
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker
from telebot import types
from models import BotWords, UsersId, AddedWords, MessagesId
from connect import connect_bot, connect_db

bot = connect_bot()

engine = connect_db()
Session = sessionmaker(engine)
session = Session()




def create_menu():
    '''Создает клавиатуру-меню'''
    markup = types.InlineKeyboardMarkup(row_width=1)
    start_btn = types.InlineKeyboardButton('Войти в игру', callback_data='play')
    add_btn = types.InlineKeyboardButton('Добавить пару слов', callback_data='add')
    del_btn = types.InlineKeyboardButton('Удалить пару слов', callback_data='delete')
    list_btn = types.InlineKeyboardButton('Посмотреть все добавленные слова', callback_data='look')
    markup.add(start_btn, add_btn, del_btn, list_btn)
    return markup

def create_clean_list(uid):
    '''
    Принимает id пользоваетеля и возвращает список id сообщений пользоваетеля
    '''
    msg_ids = session.query(MessagesId.message_id).filter(MessagesId.user_id == uid).all()
    msg_ids_delete = [m[0] for m in msg_ids]

    session.query(MessagesId).filter(MessagesId.user_id == uid).delete()
    session.commit()
    return msg_ids_delete

@bot.message_handler(commands=['start'])
def hello_massage(message):
    '''Стартовое сообщение'''
    markup = types.InlineKeyboardMarkup(row_width=1)
    menu_btn = types.InlineKeyboardButton('Меню', callback_data='menu')
    markup.add(menu_btn)
    bot.send_message(message.from_user.id, '''Привет дорогой друг.
Для того чтобы начать, надо перейти в меню, удачи!:)''', reply_markup=markup)
    

@bot.callback_query_handler(func=lambda c: c.data == 'menu')
def call_menu1(callback_query: types.CallbackQuery):
    '''
    Отправляет созданное меню в чат в ответ на CallbackQuery
    '''
    markup = create_menu()
    bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id)
    bot.send_message(callback_query.from_user.id, 'Меню:', reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Меню' or m.text == 'Закончить')
def call_menu2(message: types.Message):
    '''
    Отправляет созданное меню в чат в ответ на Message
    '''
    markup = create_menu()
    bot.send_message(message.from_user.id, 'Меню:', reply_markup=markup)



@bot.callback_query_handler(func=lambda c: c.data == 'add') 
def start_add(callback_query: types.CallbackQuery):
    '''
    Добавление пары слов в БД
    '''
    global couple_add
    couple_add = {}
    
    bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id)
    msg_input_rus = bot.send_message(callback_query.from_user.id, 'Введите слово на русском языке')
    bot.register_next_step_handler(msg_input_rus, add_rus, msg_input_rus)

def add_rus(message, msg_input_rus):
    rus_letters = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    if not rus_letters.isdisjoint(str(message.text).lower()) and message.text.isdigit() == False:
        couple_add['rus'] = message.text
        msg_input_eng = bot.send_message(message.from_user.id, 'Введите слово на английском языке')

        bot.delete_messages(chat_id=message.from_user.id, message_ids=[message.id, msg_input_rus.id])
        bot.register_next_step_handler(msg_input_eng, add_eng_and_choice, msg_input_eng)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_ok = types.InlineKeyboardButton('Вас понял, сэр', callback_data='add')
        markup.add(btn_ok)

        bot.send_message(message.from_user.id, 'Надо на русском и только буквами!', reply_markup=markup)
        
def add_eng_and_choice(message, msg2):
    eng_letters = set('abcdefghijklmnopqrstuvwxyz')
    if not eng_letters.isdisjoint(str(message.text).lower()) and message.text.isdigit() == False:
        couple_add['eng'] = message.text

        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_yes = types.InlineKeyboardButton('Да, добавить эту пару', callback_data='add_yes')
        btn_no = types.InlineKeyboardButton('Нет, поменять слова', callback_data='add')
        btn_menu = types.InlineKeyboardButton('Нет, вернуться в меню', callback_data='menu')
        markup.add(btn_yes, btn_no, btn_menu)

        bot.delete_messages(chat_id=message.from_user.id, message_ids=[message.id, msg2.id])
        bot.send_message(message.from_user.id, f'''\
Проверьте корректность введенных слов
{couple_add['rus']} - {couple_add['eng']}
Вы хотите добавить их в игру?                     
''', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_ok = types.InlineKeyboardButton('Вас понял, сэр', callback_data='add')
        markup.add(btn_ok)
        bot.send_message(message.from_user.id, 'На английском языке теперь надо было, давай по новой', reply_markup=markup)  
    
@bot.callback_query_handler(func=lambda c: c.data == 'add_yes')
def __add_couple(callback_query: types.CallbackQuery):
    uid = callback_query.from_user.id
    check = session.query(UsersId.user_id).filter(UsersId.user_id == str(uid)).first()
    if check == None:
        new_user = UsersId(user_id=uid)
        session.add(new_user)
        session.commit()
    user_id = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).first()
    check = session.query(AddedWords.id).filter(AddedWords.user_id == user_id[0], 
                                                AddedWords.rus_word == couple_add['rus'], 
                                                AddedWords.eng_word == couple_add['eng']
                                                ).first()
    if check == None:
        new_add = AddedWords(user_id=user_id[0], rus_word=str(couple_add['rus']), eng_word=str(couple_add['eng']))
        session.add(new_add)
        session.commit()

        bot.answer_callback_query(callback_query.id, text='Ваша пара успешно добавлена', show_alert=True)
        call_menu1(callback_query)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn_again = types.InlineKeyboardButton('Попробовать еще', callback_data='add')
        btn_menu = types.InlineKeyboardButton('В меню', callback_data='menu')
        markup.add(btn_again, btn_menu)

        bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.id)
        bot.send_message(callback_query.from_user.id, 'Эта пара уже добавлена', reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data == 'delete')
def start_del(callback_query: types.CallbackQuery):
    '''
    Удаление пар слов из БД
    '''
    bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id)
    msg = bot.send_message(callback_query.from_user.id, 'Введите слово чтобы удалить пару')
    bot.register_next_step_handler(msg, delete_word, msg)

def delete_word(message, msg):
    word = message.text
    uid = message.from_user.id

    sbq = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).subquery()
    check = session.query(AddedWords.id).filter(AddedWords.user_id == sbq.c.id, \
            or_(AddedWords.rus_word == word, AddedWords.eng_word == word)).first()
    if check == None:
        markup = types.InlineKeyboardMarkup(row_width=2)
        again_btn = types.InlineKeyboardButton('Попробовать еще раз', callback_data='delete')
        menu_btn = types.InlineKeyboardButton('В меню', callback_data='menu')
        markup.add(again_btn, menu_btn)

        bot.delete_messages(chat_id=message.chat.id, message_ids=[message.id, msg.id]) #!
        bot.send_message(message.from_user.id, 'Вы ввели несуществующее слово', reply_markup=markup)
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        yes_btn = types.InlineKeyboardButton('Да', callback_data='delete_yes')
        again_btn = types.InlineKeyboardButton('Нет, ввести заново', callback_data='delete')
        menu_btn = types.InlineKeyboardButton('Нет, выйти в меню', callback_data='menu')
        markup.add(yes_btn, again_btn, menu_btn)

        global couple_del
        couple_del = {}
        couple_del['rus'] = session.query(AddedWords.rus_word).filter(AddedWords.id == check[0]).first()[0]
        couple_del['eng'] = session.query(AddedWords.eng_word).filter(AddedWords.id == check[0]).first()[0]

        bot.delete_messages(chat_id=message.chat.id, message_ids=[message.id, msg.id])
        bot.send_message(message.from_user.id, f'''\
Вы хотите удалить пару
{couple_del['rus']} - {couple_del['eng']}
Вы уверены?
''', reply_markup=markup)
        
@bot.callback_query_handler(func=lambda c: c.data == 'delete_yes')
def __delete_word(callback_query: types.CallbackQuery):
    session.query(AddedWords).filter(AddedWords.rus_word == couple_del['rus'], AddedWords.eng_word == couple_del['eng']).delete()
    session.commit()

    bot.answer_callback_query(callback_query.id, 'Вы удалили пару из игры', show_alert=True)
    call_menu1(callback_query)

@bot.callback_query_handler(func=lambda c: c.data == 'look')
def look_words(callback_query: types.CallbackQuery):
    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_menu = types.InlineKeyboardButton('Меню', callback_data='menu')
    markup.add(btn_menu)

    uid = callback_query.from_user.id
    sbq = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).subquery()
    words = session.query(AddedWords.rus_word, AddedWords.eng_word).filter(AddedWords.user_id == sbq.c.id).all()

    formated_words = []
    for w in words:
        format_w = f'{w[0]} - {w[1]}'
        formated_words.append(format_w)

    bot.delete_message(chat_id=callback_query.from_user.id, message_id=callback_query.message.id)
    bot.send_message(callback_query.from_user.id, f'''\
Ваши слова:
{'\n'.join(formated_words)}                     
                     ''', reply_markup=markup)
    
@bot.callback_query_handler(func=lambda c: c.data == 'play')
def start_game(callback_query: types.CallbackQuery):
    '''
    Принимает CallbackQuery
    Вызывает ReplyKeyboard для перехода в игровой режим
    '''
    uid = callback_query.from_user.id
    check = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).first()
    if check == None:
        new_user = UsersId(user_id=str(uid))
        session.add(new_user)
        session.commit()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_btn = types.KeyboardButton('Начать')
    markup.add(start_btn)

    bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.id)
    sticker = bot.send_sticker(callback_query.from_user.id, 'CAACAgIAAxkBAAEFqnBmUNzgIZEFbKjJZTtq9Ozg3hUIzQACpzwAAjULyUv9CJLnbFrcljUE', reply_markup=markup)

    uid = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).first()[0]
    new_sticker = MessagesId(user_id=uid, message_id=sticker.id)
    session.add(new_sticker)
    session.commit()
    
    
@bot.message_handler(content_types=['text'])
def make_card(message: types.Message):
    '''
    Принимает Message
    Создает карточку для игры
    '''
    global target_eng_word

    time.sleep(0.5)
    
    if message.text == 'Начать' or message.text == 'Далее':
        bot.delete_message(chat_id=message.from_user.id, message_id=message.id)

    uid = message.from_user.id
    bot_words = session.query(BotWords.eng_word).all()
    sbq = session.query(UsersId.id).filter(UsersId.user_id == str(uid)).subquery()
    user_words = session.query(AddedWords.eng_word).filter(AddedWords.user_id == sbq.c.id).all()
    if len(user_words) > 0:
        row_words = bot_words + user_words
    else:
        row_words = bot_words

    all_words = []
    for row in row_words:
        for word in row:
            all_words.append(word)

    target_eng_word = random.choice(all_words)

    check = session.query(AddedWords.rus_word).filter(AddedWords.user_id == sbq.c.id, AddedWords.eng_word == target_eng_word).first()
    if check == None:
        target_rus_word = session.query(BotWords.rus_word).filter(BotWords.eng_word == target_eng_word).first()[0]
    else:
        target_rus_word = check[0]

    all_words.remove(target_eng_word)
    btn_list = random.choices(all_words, k=3)
    btn_list.append(target_eng_word)
    random.shuffle(btn_list)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton(btn_list[0])
    btn2 = types.KeyboardButton(btn_list[1])
    btn3 = types.KeyboardButton(btn_list[2])
    btn4 = types.KeyboardButton(btn_list[3])
    btn_menu = types.KeyboardButton('Меню')
    btn_next = types.KeyboardButton('Далее')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn_menu, btn_next)

    msg = bot.send_message(message.from_user.id, f'{target_rus_word}', reply_markup=markup)
    bot.register_next_step_handler(msg, check_choice, msg)

def check_choice(message, msg):
    '''
    Проверка выбора
    '''
    msg_id = msg.id
    uid = session.query(UsersId.id).filter(UsersId.user_id == str(message.from_user.id)).first()[0]
    new_message_id = MessagesId(user_id=uid, message_id=message.id)
    new_msg_id = MessagesId(user_id=uid, message_id=msg_id)
    session.add(new_message_id)
    session.add(new_msg_id)
    session.commit()
    if message.text == target_eng_word:
        msg_true = bot.send_message(message.from_user.id, 'Вы ответили правильно')

        new_msg_true = MessagesId(user_id=uid, message_id=msg_true.id)
        session.add(new_msg_true)
        session.commit()

        make_card(message)
    elif message.text == 'Меню':
        clean_list = create_clean_list(uid)
        bot.delete_messages(chat_id=message.chat.id, message_ids=clean_list) # удаление всей игровой сессии

        call_menu2(message)
    elif message.text == 'Далее':
        make_card(message)
    else:
        msg_false = bot.send_message(message.from_user.id, f'Не правда! Правильный ответ - {target_eng_word}')

        new_msg_false = MessagesId(user_id=uid, message_id=msg_false.id)
        session.add(new_msg_false)
        session.commit()

        make_card(message)

session.close()

if __name__ == '__main__':
    bot.infinity_polling()