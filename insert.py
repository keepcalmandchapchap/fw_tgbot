from sqlalchemy.orm import sessionmaker
from models import BotWords, create_tables
from connect import connect_db

engine = connect_db()
Session = sessionmaker(engine)
session = Session()

bot_words = {1: ('Черный', 'Black'),
             2: ('Белый', 'White'),
             3: ('Красный', 'Red'),
             4: ('Синий', 'Blue'),
             5: ('Зеленый', 'Green'),
             6: ('Желтый', 'Yellow'),
             7: ('Ты', 'You'),
             8: ('Они', 'They'),
             9: ('Оно', 'It'),
             10: ('Мы', 'We')
            }       

if __name__ == '__main__':
    create_tables(engine)

    for ind, words in bot_words.items():
        new_couple = BotWords(id=ind, rus_word=words[0], eng_word=words[1])
        session.add(new_couple)
        session.commit()    

    session.close()