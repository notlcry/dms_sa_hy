from common import singleton
from common import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@singleton
class DBNode(object):
    def __init__(self):
        db_engine = create_engine(Config().getDBUrl())
        self.session = sessionmaker(bind=db_engine)()
