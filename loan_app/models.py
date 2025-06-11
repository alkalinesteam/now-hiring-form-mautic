import os
from sqlalchemy import create_engine, Column, Integer, Float, Date
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.path.join('data', 'loan.db')
engine = create_engine(
    f'sqlite:///{DB_PATH}', connect_args={'check_same_thread': False}
)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

def get_session():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    Base.metadata.create_all(engine)
    return SessionLocal()
