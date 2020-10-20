import os
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, BigInteger, Boolean, ForeignKey, Interval, create_engine
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


def connect_to_db():
    db_username = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASS')
    db_url = os.getenv('DB_URL')
    db_port = os.getenv('DB_PORT')
    db_string = f'postgres://{db_username}:{db_password}@{db_url}:{db_port}/postgres'

    db = create_engine(db_string, pool_size=100)
    return db


Base = declarative_base()
engine = connect_to_db()


class TwitterUser(Base):
    __tablename__ = 'twitter_user'
    id = Column(BigInteger, primary_key=True)
    id_str = Column(String)
    name = Column(String)
    screen_name = Column(String)
    location = Column(String)
    url = Column(String)
    description = Column(String)
    verified = Column(Boolean)
    followers_count = Column(Integer)
    friends_count = Column(Integer)
    listed_count = Column(Integer)
    favourites_count = Column(Integer)
    statuses_count = Column(Integer)
    created_at = Column(DateTime)
    bot = Column(Boolean)

    def __repr__(self):
        return "<TwitterUser(id='%s', name='%s', screen name='%s')>" % (
            self.id, self.name, self.screen_name)


class Tweet(Base):
    __tablename__ = 'tweet'
    id = Column(BigInteger, primary_key=True)
    coordinates_lat = Column(Float)
    coordinates_long = Column(Float)
    created_at = Column(DateTime)
    created_at_in_seconds = Column(BigInteger)
    favorite_count = Column(Integer)
    favorited = Column(Boolean)
    hashtags = Column(postgresql.ARRAY(String))
    id_str = Column(String)
    in_reply_to_screen_name = Column(String)
    in_reply_to_status_id = Column(BigInteger)
    in_reply_to_user_id = Column(BigInteger)
    lang = Column(String)
    possibly_sensitive = Column(Boolean)
    quoted_status_id = Column(BigInteger)
    quoted_status_id_str = Column(String)
    retweet_count = Column(Integer)
    retweeted = Column(Boolean)
    source = Column(String)
    text = Column(String)
    truncated = Column(Boolean)
    tweet_mode = Column(String)
    urls = Column(postgresql.ARRAY(String))
    user_id = Column(BigInteger,
                     ForeignKey('twitter_user.id'),
                     nullable=True)
    user = relationship('TwitterUser')
    user_mentions = Column(postgresql.ARRAY(BigInteger))

    def __repr__(self):
        return "<Tweet(id='%s', text='%s', date='%s')>" % (
            self.id, self.text, self.created_at)


class Stock(Base):
    __tablename__ = 'stock'
    id = Column(Integer, autoincrement=True, primary_key=True)
    symbol = Column(String(5))
    short_name = Column(String)
    long_name = Column(String)
    country = Column(String)
    sector = Column(String)
    industry = Column(String)
    exchange = Column(String)
    exchange_timezone = Column(String)
    logo_url = Column(String)

    def __repr__(self):
        return "<Stock(id='%s', name='%s', symbol='%s')>" % (
            self.id, self.short_name, self.symbol)


class StockTrend(Base):
    __tablename__ = 'stock_trend'
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_id = Column(Integer,
                      ForeignKey('stock.id'),
                      nullable=False)
    stock = relationship('Stock')
    start = Column(DateTime)
    end = Column(DateTime)
    interval = Column(Interval)
    interval_desc = Column(String(6))
    open_price = Column(Float)
    close_price = Column(Float)
    price_change = Column(Float)
    price_change_pct = Column(Float)
    relative_strength = Column(Float)  # Read https://www.investopedia.com/terms/r/relativestrength.asp
    beta = Column(Float)

    def __repr__(self):
        return "<StockTrend(id='%s', stock='%s', interval='%s', end='%s')>" % (
            self.id, self.stock_id, self.interval_desc, self.end)


class SearchTerm(Base):
    __tablename__ = 'search_term'
    id = Column(Integer, autoincrement=True, primary_key=True)
    stock_id = Column(Integer,
                      ForeignKey('stock.id'),
                      nullable=False)
    stock = relationship('Stock')
    term = Column(String)

    def __repr__(self):
        return "<SearchTerm(id='%s', term='%s', stock='%s')>" % (
            self.id, self.term, self.stock)


def create_tables():
    Base.metadata.create_all(engine)


def drop_tables():
    Base.metadata.drop_all(engine)


drop_tables()
create_tables()
