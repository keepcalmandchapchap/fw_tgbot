import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class BotWords(Base):
    __tablename__ = 'bot_words'

    id = sq.Column(sq.Integer, primary_key=True)
    rus_word = sq.Column(sq.String(30), 
                         unique=True, 
                         nullable=False)
    eng_word = sq.Column(sq.String(30), 
                         unique=True, 
                         nullable=False)


class UsersId(Base):
    __tablename__ = 'users_id'

    id = sq.Column(sq.Integer, 
                   primary_key=True)
    user_id = sq.Column(sq.String(30), 
                     unique=True, 
                     nullable=False)
    

class AddedWords(Base):
    __tablename__ = 'added_words'


    id = sq.Column(sq.Integer, 
                   primary_key=True)
    user_id = sq.Column(sq.Integer, 
                        sq.ForeignKey('users_id.id'))
    rus_word = sq.Column(sq.String(30), 
                         nullable=False)
    eng_word = sq.Column(sq.String(30),
                         nullable=False)

    users_addedword = relationship(UsersId, backref='added_words')

    __table_args__ = (sq.UniqueConstraint(user_id, rus_word, eng_word), )


class MessagesId(Base):
    __tablename__ = 'messages_id'

    id = sq.Column(sq.Integer, 
                   primary_key=True)
    user_id = sq.Column(sq.Integer,
                        sq.ForeignKey('users_id.id'))
    message_id = sq.Column(sq.Integer, 
                           nullable=False, 
                           unique=True)

    users_message = relationship(UsersId, backref='messages_id')


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)




