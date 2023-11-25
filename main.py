import base64
import datetime
import json
import multiprocessing
import os
import random
import string
import sys
import threading
import time
from concurrent.futures import (ProcessPoolExecutor, ThreadPoolExecutor,
                                as_completed, wait)

import socketio
from PIL import Image
from ping3 import ping
from pystyle import *
from rich.console import Console

from ascii import *
from markov import Markov

# SocketIOテンプレ

class SocketIOClient:
    # namespace設定用
    class NamespaceClass(socketio.ClientNamespace):
        def on_connected(self):
            pass

        def on_logined_common(self):
            pass

        def on_login_failed(self):
            pass

        def on_send_friend_list(self):
            pass

        def on_got_room_list(self):
            pass

        def on_got_page(self):
            pass

        def on_sended(self):
            pass

        def on_room_created(self):
            pass

        def on_duplicate_username(self):
            pass

        def on_changed_photo(self):
            pass

        def on_changed_icon_name(self):
            pass

        def on_change_status(self):
            pass

        def on_called_ban(self):
            pass

    # 接続時
    def on_connected(self, data):
        if self.sid == None:
            #logger.debug("connected to server.")
            pass
        else:
            #logger.debug("reconnected.")
            pass
        self.event_.set()

    # ログイン･ログアウト時
    def on_logined_common(self, data):
        self.uname = data["uname"]
        self.uid = data["uid"]
        self.sid = data["sid"]
        self.character = data["character_name"]
        self.imgs = data["imgs"]
        self.img_no = data["img_no"]

        if type(self.character) is dict:
            self.character = list(data["character_name"].values())

        if self.uname == "ゲスト":
            self.uname = None
            pass
        elif data["cmd"] == "create_user":
            logger(f"{self.uname}[{self.uid}]", "created")
            account = {"uname": self.uname, "passwd": passwd, "uid": self.uid}
            json_data["accounts"].append(account)
            with open("./accounts.json", "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
        else:
            #logger.debug(
            #    f"Logined. Username: {self.uname}, Character: {self.character}, Imgs: {self.imgs}, ImgNo: {img_no}"
            #)
            account = {"uname": self.uname, "passwd": self.passwd}
            try:
                json_data["accounts"].remove(account)
                account["uid"] = self.uid
                json_data["accounts"].append(account)
                with open("./accounts.json", "w", encoding="utf-8") as f:
                    json.dump(json_data, f, indent=4, ensure_ascii=False)
            except Exception:
                pass

        self.event_.set()

    # ログイン失敗時
    def on_login_failed(self):
        self.uname = None
        self.event_.set()

    # フレンドリスト取得時
    def on_send_friend_list(self, data):
        for i in range(len(data)):
            if data[i]["on"] == 0:
                on = "Offline"
            else:
                on = "Online"
            uname = data[i]["uname"]
            print_(i+1, f"{uname}: {on}")
        self.event_.set()

    # ルームリスト取得時
    def on_got_room_list(self, data):
        room_list = list()
        for i in range(len(data["res"])):
            if i == 0:
                continue
            elif i == 15:
                break
            rname = data["res"][i]["room_name"]
            rid = data["res"][i]["_id"]
            room_list.append(rid)
            print(f"[{i-1}] RoonName: {rname}, RoomID: {rid}")
        i = int(input("入室するルームを選択(99: 選択しない)\n> "))
        if i != 99:
            try:
                rid = room_list[i]
            except IndexError:
                pass
            else:
                print(rid)
                self.emitJoin({"room_id": rid, "page": 0, "passwd": "", "answer": ""})
        self.event_.set()

    # ルーム入室時
    def on_got_page(self, data):
        try:
            rid = data["res2"][0]["room_id"]
        except IndexError:
            rid = data["room_id"]
        #logger.debug(f"Joined room. RoomID: {rid}, Username: {self.uname}")
        self.ban = False
        self.rid = rid
        logger(f"{self.uname}@{self.uid}", "joined")
        #print(f"{self.uname}@{self.uid}", file=sys.stderr)
        self.event_.set()

    def on_sended(self, data):
        #logger_(f"{self.uname}[{self.uid}]", "sent")
        pass

    # ルーム作成時
    def on_room_created(self, data):
        rid = data["room_id"]
        logger(self.uid, "created")
        self.event_.set()

    # ユーザーネーム被り時
    def on_duplicate_username(self, data):
        uname = data["uname"]
        #logger.debug(f"{uname} is duplicate username.")
        self.event_.set()

    # アイコン変更時
    def on_changed_photo(self, data):
        uname = data["uname"]
        self.imgs = data["imgs"]
        array_no = int(data["selected_array_no"])
        self.img_no = self.imgs[array_no]
        #logger.debug(f"Changed Photo. User: {uname}, Imgs: {self.imgs}, ImgNo: {img_no}")
        logger(f"{self.uname}@{self.uid}", "changed")
        self.event_.set()

    # アイコン/キャラ名変更時
    def on_changed_icon_name(self, data):
        self.character = list(data["character_name"].values())
        self.event_.set()

    def on_change_status(self, data):
        self.event_.set()

    # BAN
    def on_called_ban(self, data):
        logger(f"{self.uname}@{self.uid}", "banned")
        pass

    # namespaceクラスオーバーライド
    def overload_event(self):
        self.Namespace.on_connected = self.on_connected
        self.Namespace.on_logined_common = self.on_logined_common
        self.Namespace.on_login_failed = self.on_login_failed
        self.Namespace.on_send_friend_list = self.on_send_friend_list
        self.Namespace.on_got_room_list = self.on_got_room_list
        self.Namespace.on_got_page = self.on_got_page
        self.Namespace.on_sended = self.on_sended
        self.Namespace.on_room_created = self.on_room_created
        self.Namespace.on_duplicate_username = self.on_duplicate_username
        self.Namespace.on_changed_photo = self.on_changed_photo
        self.Namespace.on_changed_icon_name = self.on_changed_icon_name
        self.Namespace.on_change_status = self.on_change_status
        self.Namespace.on_called_ban = self.on_called_ban

    # 初期化
    def __init__(self, namespace):
        self.rid = None
        self.sid = None
        self.uid = None
        self.bid = None
        self.uname = None
        self.passwd = None
        self.character = None
        self.imgs = None
        self.img_no = None

        self.namespace_ = namespace
        self.sio_ = socketio.Client()
        self.Namespace = self.NamespaceClass(self.namespace_)
        self.overload_event()
        self.sio_.register_namespace(self.Namespace)
        self.event_ = threading.Event()

    # 接続
    def connect(self):
        self.sio_.connect("https://netroom.co.jp")
        self.event_.wait()
        # print(
        #    f"connected to server.\n{self.ip_}:{self.port_}, namespace={self.namespace_}")

    # 切断
    def disconnect(self):
        self.sio_.disconnect()

    # ログイン
    def emitLogin(self, data):
        self.passwd = data["passwd"]
        self.bid = data["bid"]
        self.sio_.emit(
            "login", data, callback=(self.on_logined_common, self.on_login_failed)
        )
        self.event_.wait()
        self.event_.clear()

    # ログアウト
    def emitLogout(self, data):
        self.sio_.emit("logout", data, callback=self.on_logined_common)
        self.event_.wait()
        self.event_.clear()

    # フレンドリスト
    def emitFriendList(self):
        self.sio_.emit("get_friend_list")
        self.event_.wait()

    # ルームリスト
    def emitRoomList(self, data):
        self.sio_.emit("get_room_list", data, callback=self.on_got_room_list)
        self.event_.wait()

    # ルーム入室
    def emitJoin(self, data):
        if data["room_id"] == "0":
            self.sio_.emit("join", data)
            logger(f"{self.uname}@{self.uid}", "left")
        else:
            self.sio_.emit("join", data, callback=self.on_got_page)
            self.event_.wait()
        self.event_.clear()


    # メッセージ送信
    def emitSend(self, data):
        self.sio_.emit("send", data, callback=self.on_sended)

    # DM送信
    def emitPrivateMessage(self, data):
        self.sio_.emit("send_pvt_message", data)

    # ルーム作成
    def emitCreateRoom(self, data):
        self.sio_.emit("create_room", data, callback=self.on_room_created)
        self.event_.wait()
        self.event_.clear()

    # アカウント作成
    def emitCreateUser(self, data):
        self.sio_.emit(
            "create_user",
            data,
            callback=(self.on_logined_common, self.on_duplicate_username),
        )
        self.event_.wait()
        self.event_.clear()

    # アイコン変更
    def emitChangeProfile(self, data):
        self.sio_.emit("change_profile", data, callback=self.on_changed_photo)
        self.event_.wait()
        self.event_.clear()

    # アイコン･キャラ名変更
    def emitChangeIconName(self, data):
        self.sio_.emit("change_icon_name", data)
        self.event_.wait()
        character = data["character_name"]
        print(f"Changed Character: {character}")

    def emitChangeStatus(self, data):
        self.sio_.emit("change_status", data, callback=self.on_change_status)
        self.event_.wait()
        logger(f"{self.uname}@{self.uid}", "status")
        self.event_.clear()

    # メイン処理
    def run(self):
        self.connect()
        #print(self.sio_.sid)
        # p = threading.Thread(target=self.sio_.wait)
        # p.setDaemon(True)
        # p.start()
        self.event_.clear()

def titlebar():
    count = 600
    while True:
        global titlebar_kill
        if titlebar_kill:
            break
        if count == 600:
            try:
                ping_ = int(ping("netroom.co.jp", unit="ms"))
            except Exception:
                ping_ = 0
            System.Title(f"KATYUKUSA {version} ｜ Accounts: [{len(accounts)}] ｜ Ping: [{ping_}ms] ｜ Proxies: [0]")
            count = 0
            time.sleep(0.1)
        else:
            count = count+1
            time.sleep(0.1)



def account_list():
    print("-" * 15, "Account List", "-" * 15)
    for i in range(len(accounts)):
        uname = accounts[i]["uname"]
        print_(i, uname)


def prefix(data, count):
    if "!random" in data:
        for i in range(count):
            randstr = "".join(
                random.choices(string.ascii_letters + string.digits, k=10)
            )
            data_ = data.replace("!random", randstr)
            yield data_
    elif "!markov" in data:
        file = "wagahaiwa_nekodearu.txt"
        markov = Markov(file, 15, 2)
        markov.main()
        for i in range(count):
            while True:
                try:
                    sentence = markov.make_sentence()
                    data_ = data.replace("!markov", sentence)
                except KeyError:
                    pass
                else:
                    break
            yield data_
    else:
        for i in range(count):
            yield data


def print_(mark, message):
    return console.print(f"[yellow1][[/yellow1]{mark}[yellow1]][/yellow1] {message}", highlight=False)

def input_(mark, message):
    return console.input(f"[yellow][[/yellow]{mark}[yellow]][/yellow] {message.replace('> ', '[yellow1]> [/yellow1]')}")

def logger(message, status):
    if status == "failed" or status == "invalid" or status == "banned":
        status = f"[red1][{status.upper()}][/red1]"
        mark = "[yellow1][[/yellow1][red1]-[/red1][yellow1]][/yellow1]"
    else:
        status = f"[green1][{status.upper()}][/green1]"
        mark = "[yellow1][[/yellow1][green1]+[/green1][yellow1]][/yellow1]"
    dt = datetime.datetime.now().time()
    return console.print(f"{mark}[yellow1][[/yellow1][d]{str(dt)[0:8]}[/d][yellow1]][/yellow1] {message} {status}", highlight=False)

def img2b64(path):
    with open(path, "rb") as img:
        data = base64.b64encode(img.read())
        img = Image.open(path)
        data = f"data:image/{img.format.lower()};base64,{data.decode('utf-8')}"

    return data


def randStr(key=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=key))

def friendSpam(uid: str, accounts: list):
    client = SocketIOClient("/")
    client.run()
    for account in accounts:
        bid = randStr()
        # ログインデータ送信
        client.emitLogin(
            {
                "uname": account["uname"],
                "passwd": account["passwd"],
                "bid": bid,
                "sid": "",
                "keep_login": "0",
            }
        )
        if client.uname != None or client.uname == "ゲスト":
            try:
                img_no = random.choice(client.imgs)
            except Exception:
                img_no = 0
            client.emitPrivateMessage(
                {
                    "selected_uid": uid,
                    "msg": "",
                    "pvm_type": 2,
                    "img_no": img_no,
                }
            )
            logger(f"{client.uname}@{client.uid}", "sent")
            client.emitLogout({"bid": bid, "sid": client.sid})
        else:
            try:
                account["uid"]
            except Exception:
                logger(f"{account['uname']}", "failed")
            else:
                logger(f"{account['uname']}[{account['uid']}]", "failed")


def login_(account):
    global clients
    client = SocketIOClient("/")
    client.run()
    bid = randStr()
    client.emitLogin(
        {
            "uname": account["uname"],
            "passwd": account["passwd"],
            "bid": bid,
            "sid": "",
            "keep_login": "0",
        }
    )
    if client.uname == None or client.uname == "ゲスト":
        logger(f"{account['uname']}@{account['uid']}", "failed")
    else:
        logger(f"{client.uname}@{client.uid}", "logged")
    clients.append(client)

def logout(client: SocketIOClient):
    global clients
    uname = client.uname
    uid = client.uid
    client.emitLogout({"bid": client.bid, "sid": client.sid})
    logger(f"{uname}@{uid}", "logged")
    client.disconnect()
    clients.remove(client)

def extraStatus():
    def changeStatus(client, randstr_list):
        while True:
            for randstr in randstr_list:
                client.emitChangeStatus({"status": randstr, "room_id": "0"})
    randstr_list = [randStr(15) for i in range(10)]
    with ThreadPoolExecutor() as executor:
        tasks = [executor.submit(changeStatus, client, randstr_list) for client in clients]
        wait(tasks, return_when="ALL_COMPLETED")

def join(client: SocketIOClient, rid):
    #time.sleep(0.05)
    client.emitJoin({"room_id": rid, "page": 0, "passwd": "", "answer": ""})

def leave(client: SocketIOClient):
    client.emitJoin({"roomd_id": "0", "page": 0, "passwd": "", "answer": ""})

def join_(account: dict, rid: str):
    client = SocketIOClient("/")
    client.run()
    bid = randStr()
    client.emitLogin(
        {
            "uname": account["uname"],
            "passwd": account["passwd"],
            "bid": bid,
            "sid": "",
            "keep_login": "0"
        }
    )
    if client.uname != None:
        client.emitJoin({"room_id": rid, "page": 0, "passwd": "", "answer": ""})
        logger(f"{client.uname}@{client.uid}", "joined")
    else:
        logger(f"{account['uname']}@{account['uid']}", "failed")

def spam(client: SocketIOClient, message: str, count: int):
    for message_ in prefix(message, count):
        time.sleep(0.01)
        if client.ban:
            break
        img_no = random.choice(client.imgs)
        if client.character == "":
            character = ""
        else:
            character = random.choice(client.character)
        client.emitSend(
            {
                "comment": message_,
                "type": "1",
                "room_id": client.rid,
                "img": "",
                "img_no": img_no,
                "character_name": character,
            }
        )
        logger(f"{client.uname}@{client.uid}", "sent")

if getattr(sys, 'frozen', False):
    # 実行ファイルからの実行時
    script_dir = sys._MEIPASS
else:
    # スクリプトからの実行時
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("./accounts.json", "r", encoding="utf-8") as f:
    json_data = json.load(f)

accounts = json_data["accounts"]
clients = list()
console = Console(stderr=True)
version = "v1.1"
titlebar_ = threading.Thread(target=titlebar)
titlebar_kill = False
titlebar_.start()
extrastatus = threading.Thread(target=extraStatus)

if __name__ == "__main__":
    System.Clear()

    print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(banner), 1))
    # print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter("Author: k2angel"), 1))

    print_("#", "Welcome to Katyukusa.")
    # SocketIOClientインスタンス搾精
    sio_client = SocketIOClient("/")
    try:
        # SocketIOClientインスタンス実行
        sio_client.run()
        pass
    except Exception as e:
        print_("!", "Failed connect server!")
        input_("#", "Press ENTER to exit.")
        titlebar_kill = True
        titlebar_.join()
        System.Clear()
        exit()
    else:
        print_("#", "Successfully connected server!")
        sio_client.disconnect()
        del sio_client
    input()
    System.Clear()
    while True:
        print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(banner), 1))
        try:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(menu), 1))
            mode = int(input_("#", "> "))
        except Exception:
            print_("!", "Error.")
            input_("#", "Press ENTER to go back.")
            System.Clear()
            continue
        System.Clear()
        #for client in clients:
        #    try:
        #        client.connect()
        #    except Exception:
        #        pass
        if mode == 1:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(login_banner), 1))
            if len(accounts) != 1:
                accounts_ = list()
                raid = input_("RAID", "> ")
                if raid == "y":
                    count = int(input_("ACCOUNT", "> "))
                    for i in range(count):
                        account = random.choice(accounts)
                        accounts_.append(account)
                else:
                    mode_ = input_("?", "Choose account > ")
                    if mode_ == "y":
                        account_list()
                        i = int(input_("#", "> "))
                        accounts_.append(accounts[i])
                    else:
                        accounts_.append(random.choice(accounts))
                with ThreadPoolExecutor() as executor:
                    tasks = [executor.submit(login_, account) for account in accounts_]
                    wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 2:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(logout_banner), 1))
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(logout, client) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 3:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(generator_banner), 1))
            # アカウント作成
            uname = input_("?", "Account name > ")
            mode_ = input_("?", "Add profile icon > ")
            if mode_ == "y":
                path = input_("IMAGE", "> ")
                img = img2b64(path)
            count = int(input_("COUNT", "> "))
            for i in range(count):
                bid = randStr()
                passwd = randStr()
                while True:
                    if count > 1 or sio_client.uname == "ゲスト":
                        uname_ = f"{uname} {randStr()}"
                    else:
                        uname_ = uname
                    sio_client.emitCreateUser(
                        {
                            "bid": bid,
                            "keep_login": "0",
                            "passwd": passwd,
                            "uname": uname_,
                        }
                    )
                    if sio_client.uname == None:
                        logger(f"{account['uname']}[{account['uid']}]", "failed")
                        continue
                    if mode_ == "y":
                        sio_client.emitChangeProfile(
                            {
                                "img": img,
                                "info": "",
                                "room_id": "0",
                                "img_command": "change",
                                "selected_my_icon": "0",
                            }
                        )
                    sio_client.emitLogout({"bid": bid, "sid": sio_client.sid})
                    break
        elif mode == 4:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(icon_banner), 1))
            path = input_("IMAGE", "> ")
            img = img2b64(path)
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(client.emitChangeProfile, {"img": img,"info": "","room_id": "0","img_command": "change","selected_my_icon": client.img_no}) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
            #logger(sio_client.uname, "added")
        elif mode == 6:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(status_banner), 1))
            status = input_("STATUS", "> ")
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(client.emitChangeStatus,{"status": status, "room_id": "0"}) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 7:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(health_banner), 1))
            total = len(accounts)
            valid = 0
            invalid = 0
            for account in accounts:
                bid = randStr()
                sio_client.emitLogin(
                    {
                        "uname": account["uname"],
                        "passwd": account["passwd"],
                        "bid": bid,
                        "sid": "",
                        "keep_login": "0",
                    }
                )
                if sio_client.uname == None:
                    invalid = invalid + 1
                    json_data["accounts"].remove(account)
                    with open("./accounts.json", "w", encoding="utf-8") as f:
                        json.dump(json_data, f, indent=4, ensure_ascii=False)
                    if "uid" in account:
                        logger(f"{account['uname']}[{account['uid']}]", "invalid")
                    else:
                        logger(f"{account['uname']}", "invalid")
                else:
                    valid = valid + 1
                    logger(f"{sio_client.uname}@{sio_client.uid}", "invalid")
                    sio_client.emitLogout({"bid": bid, "sid": sio_client.sid})
            else:
                print("-" * 15)
                print(f"  Total: {total}\n  Valid: {valid}\n  Invalid: {invalid}")
                print("-" * 15)

            with open("./accounts.json", "r", encoding="utf-8") as f:
                json_data = json.load(f)

            accounts = json_data["accounts"]
        elif mode == 8:
            account_list()
        elif mode == 10:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(join_banner), 1))
            # ルーム入室
            rid = input_("ID", "> ")
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(join, client, rid) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 11:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(leave_banner), 1))
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(join, client, "0") for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 12:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(create_banner), 1))

            # ルーム作成
            rname = input_("NAME", "> ")
            rdesc = input_("DESCRIPTION", "> ")
            count = int(input_("COUNT", "> "))
            for i in range(count):
                rstr = randStr()
                sio_client.emitCreateRoom(
                    {
                        "room_name": rname + rstr,
                        "room_desc": rdesc,
                        "category": "野球",
                        "r_permition": "0",
                        "w_permition": "0",
                        "room_passwd": "",
                        "room_riddle": "",
                        "room_answer": "",
                    }
                )
        elif mode == 13:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(list_banner), 1))
            # ルームリスト取得
            sio_client.emitRoomList(
                {"category": "", "room_name": "", "update_time": ""}
            )
        elif mode == 20:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(message_banner), 1))
            # メッセージ送信
            message = input_("MESSAGE", "> ")
            # img = int(input("画像を送信するか(0: する, 1: しない)\n>"))
            count = int(input_("COUNT", "> "))
            # start = time.time()
            # tqdm(range(count), desc="Spam"):
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(spam, client, message, count) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 22:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(friend_banner), 1))
            uid = input_("UID", "> ")
            max_process = int(len(accounts) / 30)
            accounts_list = [accounts[idx:idx+max_process] for idx in range(0, len(accounts), max_process)]
            with ProcessPoolExecutor() as executor:
                tasks = [executor.submit(friendSpam, uid, accounts) for accounts in accounts_list]
                wait(tasks, return_when="ALL_COMPLETED")
        elif mode == 30:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(friendlist_banner), 1))
            # フレンドリスト取得
            sio_client.emitFriendList()
        elif mode == 31:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(proxy_banner), 1))
            print_("!", "Proxy is not implementation.")
        elif mode == 34:
            print_("!", "ExtaraStatus is not implementation.")
            """
            if not extrastatus.is_alive():
                extrastatus.start()
            else:
                extrastatus.join()"""
        elif mode == 33:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(test_banner), 1))
            print_("#", "Raid test.")
            rid = "95285"#input_("RID", "> ")
            accounts_ = list()
            for i in range(5):
                account = random.choice(accounts)
                accounts_.append(account)
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(login_, account) for account in accounts_]
                wait(tasks, return_when="ALL_COMPLETED")
            with ThreadPoolExecutor() as executor:
                tasks = [executor.submit(join, client, rid) for client in clients]
                wait(tasks, return_when="ALL_COMPLETED")

            #for client in clients:
            #    multiprocessing.Process(target=join, args=[client, "101212"])
        elif mode == 34:
            print(Colorate.Vertical(Colors.yellow_to_red, Center.XCenter(exit_banner), 1))
            # 切断
            for client in clients:
                client.disconnect()
                clients.remove(client)
            titlebar_kill = True
            titlebar_.join()
            System.Clear()
            # 終了
            sys.exit()
        input_("#", "Press ENTER to go back.")
        System.Clear()