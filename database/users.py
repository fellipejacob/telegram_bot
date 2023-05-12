from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    gender = Column(String)
    photo = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    bio = Column(String)

    def __repr__(self):
        return f"<User(chat_id='{self.chat_id}', gender='{self.gender}', photo='{self.photo}', latitude='{self.latitude}', longitude='{self.longitude}', bio='{self.bio}')>"


engine = create_engine('sqlite:///user_data.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

user = User()
