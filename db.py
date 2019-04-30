import os
import time
import shutil

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import create_engine


Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    nick = Column(String)
    fullname = Column(String)
    time_start = Column(Integer)
    last_msg = Column(String)

    def __init__(self, user_id, nick, fullname, time_start=None):
        self.user_id = user_id
        self.nick = nick
        self.fullname = fullname

        if time_start is not None:
            self.time_start = time_start
        else:
            self.time_start = int(time.time())
        self.last_msg = None

    def __repr__(self):
        return f"<User(user_id={self.user_id}, nick={self.nick}, name={self.fullname}, time_start={self.time_start})>"



class DB:
    def __init__(self, filename, only_read=False, debug=False):
        path = os.path
        if path.isfile(filename) and not only_read:
            data_dir = path.dirname(filename)
            fname = path.basename(filename)
            backup_file = path.join(data_dir, "backups", fname)
            backup_file += "_{}".format(int(time.time()))
            print("Copying {} to {}".format(filename, backup_file))
            shutil.copy(filename, backup_file)

        self.engine = create_engine(
            'sqlite:///{}'.format(filename),
            connect_args={'check_same_thread': False},
            echo=debug
        )
        Session = scoped_session(sessionmaker(bind=self.engine))
        self.session = Session()

        Base.metadata.create_all(self.engine)

    def add_record(self, obj, do_flush=True):
        self.session.add(obj)
        if do_flush:
            self.flush()

    def flush(self):
        self.session.commit()
        self.session.flush()




class UserDB(DB):
    def __init__(self, db):
        self.session = db.session
        all_users = self.session.query(User).all()
        self.users = {user.user_id: user for user in all_users}
        print("Loaded {} users".format(len(self.users)))

    def try_create(self, user_id, nick, fullname):
        if user_id in self.users:
            return
        user = User(user_id=user_id, nick=nick, fullname=fullname)
        self.users[user_id] = user
        self.add_record(user)

    def get_all(self):
        return self.users.values()

    def get_by_id(self, user_id):
        return self.users.get(user_id, None)

    def get_by_update(self, update):
        return self.get_by_id(update._effective_user.id)


if __name__ == "__main__":
    # A little testing
    base = DB("data/test.sqlite")
    user_db = UserDB(base)
    user_db.try_create(2332, "asa", "fdfs")
    print(user_db.get_all())
