import json
import time
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

LOG_FILENAME = "data/json_log_file.txt"

print(f"WARNING: I log everything to {LOG_FILENAME}")
JSON_LOG_FILE = open(LOG_FILENAME, "a")


class MyUpdate:
    def __init__(self, update, func_name=None):
        self.update_json = None
        self.nick = None
        self.fullname = None
        self.user_id = None
        self.cmd = None
        self.update = update
        self.func_name = func_name
        self.my_time = int(time.time())

        self._prepare_json()
        self._parse_user()
        self._parse_cmd()

    def _prepare_json(self):
        _json = json.loads(self.update.to_json())
        _json["func_name"] = self.func_name
        _json["my_time"] = self.my_time
        self.update_json = _json

    def _parse_user(self):
        user = self.update_json["_effective_user"]
        nick = user.get("username", "")
        fullname = u"{} {}".format(user.get("first_name", "-"), user.get("last_name", ""))
        fullname = fullname.strip()
        if nick == "":
            nick = "@ " + fullname
        
        self.nick = nick
        self.fullname = fullname
        self.user_id = user["id"]


    def _parse_cmd(self):
        data = self.update_json  
        cmd = u"{} {}".format(data.get('callback_query', {}).get("data", ""), 
               data.get('message', {}).get("text", ""))
        self.cmd = cmd.strip()

    def __repr__(self):
        return f"<MyUpdate(user_id= {self.user_id}, nick= {self.nick}, name= {self.fullname}, func= {self.func_name}, cmd= {self.cmd}, time= {self.my_time})>"

    def json(self):
        return self.update_json


def log_update(func_name, update):
    my_update = MyUpdate(update, func_name)

    s = json.dumps(my_update.json()) + "\n"
    JSON_LOG_FILE.write(s)
    JSON_LOG_FILE.flush()

    logger.warning(f"CALL:  {my_update}")
    return my_update
