from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from envparse import env

env.read_envfile('.env')
DATABASE_URL = env.str('DATABASE_URL', default='sqlite:///chatbot.db')

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    fullname = Column(String, nullable=False)
    email = Column(String, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, fullname={self.fullname}, email={self.email})>"

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def db_session():
    return SessionLocal()

def register_user(fullname: str, email: str):
    """
    Функция добавляет нового пользователя в базу данных.
    """
    with db_session() as session:
        user = User(fullname=fullname, email=email)
        session.add(user)
        session.commit()
        return user
