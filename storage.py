import logging
import json
import os
from prometheus_client import Counter
from sqlalchemy import exists
from db import TwitterUser, Tweet

REDIS_KEY = os.getenv('REDIS_KEY', 'tweets')
TWEETS_PER_PULL = os.getenv('tweets_per_pull', 100)
TWEETS_PROCESSED = Counter('tweets_processed', '# of Tweets inserted into the DB by the consumer')


class Storage(object):
    """
    This class retrieves Tweets from Redis and stores them in a SQL DB
    Args:
        sql_session: SQLAlchemy db session
        redis_session: Redis db session
    """

    def __init__(self, sql_session, redis_session):
        self.sql_session = sql_session
        self.redis_session = redis_session

        self.tweets = None
        self.inserts = []
        self.insert_ids = []
        self.user_updates = []
        self.user_update_ids = []
        self.tweet_updates = []
        self.tweet_update_ids = []

    def read_from_redis(self):
        """
        Pulls Tweets from Redis
        For a deeper explanation of this function, please read:
            https://dev.to/ahf90/atomically-popping-multiple-items-from-a-redis-list-in-python-2afa
        """
        blocking_result = self.redis_session.blpop(REDIS_KEY)
        pipe = self.redis_session.pipeline()
        pipe.lrange(REDIS_KEY, 0, TWEETS_PER_PULL)
        pipe.ltrim(REDIS_KEY, TWEETS_PER_PULL + 1, -1)
        result = pipe.execute()
        self.tweets = result[0] + [blocking_result[1]]
        logging.info(f'Found {len(self.tweets)} tweets')

    def store_data(self):
        for result in self.tweets:
            result = json.loads(result.decode('utf-8'))
            self.store_user(result['user'])
            self.store_tweet(result)

    def store_user(self, user):
        new_user = TwitterUser()
        for column in TwitterUser.__table__.columns:
            if column.name == 'bot':
                setattr(new_user, column.name, False)
            else:
                setattr(new_user, column.name, user.get(column.name))

        if self.sql_session.query(exists().where(TwitterUser.id == new_user.id)).scalar():
            if new_user.id not in self.user_update_ids:
                self.user_updates.append(new_user.__dict__)
                self.user_update_ids.append(new_user.id)
        else:
            if new_user.id not in self.insert_ids:
                self.inserts.append(new_user)
                self.insert_ids.append(new_user.id)

    def store_tweet(self, tweet):
        new_tweet = Tweet()
        for column in Tweet.__table__.columns:
            if column.name == 'hashtags':
                obj_properties = [obj.get('text') for obj in tweet.get(column.name)]
                setattr(new_tweet, column.name, obj_properties)
            elif column.name == 'user_id':
                setattr(new_tweet, column.name, tweet['user']['id'])
            elif column.name == 'urls':
                obj_properties = [obj.get('url') for obj in tweet.get(column.name)]
                setattr(new_tweet, column.name, obj_properties)
            elif column.name == 'user_mentions':
                obj_properties = [obj.get('id') for obj in tweet.get(column.name)]
                setattr(new_tweet, column.name, obj_properties)
            else:
                try:
                    setattr(new_tweet, column.name, tweet.get(column.name))
                except AttributeError:
                    pass

        if self.sql_session.query(exists().where(Tweet.id == new_tweet.id)).scalar():
            if new_tweet.id not in self.tweet_update_ids:
                self.tweet_updates.append(new_tweet.__dict__)
                self.tweet_update_ids.append(new_tweet.id)
        else:
            if new_tweet.id not in self.insert_ids:
                self.inserts.append(new_tweet)
                self.insert_ids.append(new_tweet.id)

    def save_objects(self):
        self.sql_session.bulk_save_objects(self.inserts)
        self.sql_session.bulk_update_mappings(Tweet, self.tweet_updates)
        self.sql_session.bulk_update_mappings(TwitterUser, self.user_updates)
        self.sql_session.flush()
        self.sql_session.commit()
        self.sql_session.close()
        num_inserts = len(self.inserts)
        num_tweet_updates = len(self.tweet_updates)
        num_user_updates = len(self.user_updates)
        logging.info(f'Saved {num_inserts} tweets and users', extra={'db_inserts': num_inserts})
        logging.info(f'Updated {num_tweet_updates} tweets', extra={'tweets_updated': num_tweet_updates})
        logging.info(f'Updated {num_user_updates} users', extra={'users_updated': num_user_updates})
