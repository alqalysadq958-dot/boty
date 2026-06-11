# لعبة حرب الممالك - نسخة تعمل كخدمة مستقلة
# DEV @TVXSSS

import os
import time
import json
import random
import sqlite3
import requests
from datetime import datetime
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, ChatMemberHandler, Filters, CallbackContext

avetaar_token = "8066045599:AAGzqyjDeBsBhKpfArpteUNrZtJYeEmf4sg"
dev_avetaar_id = 7939265907
avetaar_support_channel = "@sadeiq"
avetaar_dev_username = "@TVXSSS"

class AvetaarUltimateDatabase:
    def __init__(self):
        self.avetaar_db_path = "avetaar_universe.db"
        self.avetaar_base_dir = "Avetaar_Kingdoms_Data"
        self.avetaar_conn = sqlite3.connect(self.avetaar_db_path, check_same_thread=False)
        self.avetaar_cursor = self.avetaar_conn.cursor()
        self.avetaar_setup()

    def avetaar_setup(self):
        if not os.path.exists(self.avetaar_base_dir):
            os.makedirs(self.avetaar_base_dir)
        self.avetaar_cursor.execute("""
            CREATE TABLE IF NOT EXISTS avetaar_users (
                user_id INTEGER PRIMARY KEY, username TEXT, total_xp INTEGER DEFAULT 0, gold INTEGER DEFAULT 100,
                mine_count INTEGER DEFAULT 0, last_mine REAL DEFAULT 0, current_kingdom INTEGER DEFAULT 0,
                join_date TEXT, title TEXT DEFAULT '', skill_atk INTEGER DEFAULT 0, skill_mine INTEGER DEFAULT 0,
                skill_dodge INTEGER DEFAULT 0, secret_stash INTEGER DEFAULT 0, pet TEXT DEFAULT 'لا يوجد',
                quests_completed INTEGER DEFAULT 0, is_pow INTEGER DEFAULT 0, magic_buff TEXT DEFAULT '',
                is_sick INTEGER DEFAULT 0, job TEXT DEFAULT 'باطل', bounty INTEGER DEFAULT 0,
                bank_deposit INTEGER DEFAULT 0, hidden_gold INTEGER DEFAULT 0, jail_time REAL DEFAULT 0
            )
        """)
        self.avetaar_cursor.execute("""
            CREATE TABLE IF NOT EXISTS avetaar_kingdoms (
                chat_id INTEGER PRIMARY KEY, kingdom_id TEXT UNIQUE, name TEXT, emperor_id INTEGER,
                min_def INTEGER DEFAULT 0, min_eco INTEGER DEFAULT 0, min_int INTEGER DEFAULT 0,
                treasury INTEGER DEFAULT 1000, tax_rate INTEGER DEFAULT 30, shield_until REAL DEFAULT 0,
                siege_until REAL DEFAULT 0, ally_id INTEGER DEFAULT 0, loan_amount INTEGER DEFAULT 0,
                mercs_until REAL DEFAULT 0, hospital_lvl INTEGER DEFAULT 0, is_dark_age INTEGER DEFAULT 0,
                happiness INTEGER DEFAULT 100, is_colony_of INTEGER DEFAULT 0, artifact TEXT DEFAULT '',
                wonder TEXT DEFAULT '', farms_lvl INTEGER DEFAULT 0
            )
        """)
        self.avetaar_cursor.execute("""
            CREATE TABLE IF NOT EXISTS avetaar_citizens (
                user_id INTEGER, chat_id INTEGER, rank TEXT DEFAULT 'جندي',
                inventory TEXT DEFAULT '{}', is_spy_for INTEGER DEFAULT 0, weapon_lvl INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        self.avetaar_cursor.execute("""
            CREATE TABLE IF NOT EXISTS avetaar_global (
                id INTEGER PRIMARY KEY, boss_hp INTEGER DEFAULT 0, boss_max_hp INTEGER DEFAULT 100000,
                crypto_price INTEGER DEFAULT 100, inflation_rate REAL DEFAULT 1.0
            )
        """)
        self.avetaar_cursor.execute("INSERT OR IGNORE INTO avetaar_global (id, boss_hp) VALUES (1, 0)")
        self.avetaar_conn.commit()

    def avetaar_sync_files(self, avetaar_chat_id: int, avetaar_name: str, avetaar_kid: str):
        avetaar_kdir = os.path.join(self.avetaar_base_dir, f"Kingdom_{avetaar_kid}")
        os.makedirs(avetaar_kdir, exist_ok=True)
        avetaar_info = os.path.join(avetaar_kdir, "data.json")
        if not os.path.exists(avetaar_info):
            with open(avetaar_info, 'w', encoding='utf-8') as f:
                json.dump({"name": avetaar_name, "chat_id": avetaar_chat_id, "created": str(datetime.now())}, f, ensure_ascii=False)
        open(os.path.join(avetaar_kdir, "traitors.txt"), 'a').close()
        open(os.path.join(avetaar_kdir, "crimes.txt"), 'a').close()

    def avetaar_fetch_query(self, query, args=()):
        self.avetaar_cursor.execute(query, args)
        return self.avetaar_cursor.fetchone()

    def avetaar_fetch_all(self, query, args=()):
        self.avetaar_cursor.execute(query, args)
        return self.avetaar_cursor.fetchall()

    def avetaar_exec_query(self, query, args=()):
        self.avetaar_cursor.execute(query, args)
        self.avetaar_conn.commit()

    def avetaar_register_global(self, uid: int, uname: str):
        if not self.avetaar_fetch_query("SELECT user_id FROM avetaar_users WHERE user_id = ?", (uid,)):
            self.avetaar_exec_query("INSERT INTO avetaar_users (user_id, username, join_date) VALUES (?, ?, ?)", (uid, uname, str(datetime.now())))

    def avetaar_init_kingdom(self, chat_id: int, name: str, emp_id: int) -> str:
        res = self.avetaar_fetch_query("SELECT kingdom_id FROM avetaar_kingdoms WHERE chat_id = ?", (chat_id,))
        if res: return res[0]
        kid = f"KND-{random.randint(100000, 999999)}"
        self.avetaar_exec_query("INSERT INTO avetaar_kingdoms (chat_id, kingdom_id, name, emperor_id) VALUES (?, ?, ?, ?)", (chat_id, kid, name, emp_id))
        self.avetaar_sync_files(chat_id, name, kid)
        return kid

    def avetaar_log_traitor(self, kid, name, to_kingdom):
        traitor_path = os.path.join(self.avetaar_base_dir, f"Kingdom_{kid}", "traitors.txt")
        with open(traitor_path, 'a', encoding='utf-8') as f:
            f.write(f"{name} -> {to_kingdom} at {datetime.now()}\n")

class AvetaarUltimateEngine:
    def __init__(self, db: AvetaarUltimateDatabase):
        self.avetaar_db = db

    def avetaar_get_title(self, gold: int, xp: int) -> str:
        if gold > 100000: return "قارون"
        if xp > 50000: return "سفاح"
        return "مواطن"

    def avetaar_update_happiness(self, cid: int):
        k = self.avetaar_db.avetaar_fetch_query("SELECT tax_rate, happiness FROM avetaar_kingdoms WHERE chat_id = ?", (cid,))
        if not k: return
        tax, hap = k[0], k[1]
        if tax > 40: new_hap = max(0, hap - int((tax - 40)/2))
        elif tax < 20: new_hap = min(100, hap + 5)
        else: new_hap = hap
        self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET happiness = ? WHERE chat_id = ?", (new_hap, cid))

    def avetaar_process_tax(self, uid: int, cid: int, amount: int, evade: bool = False) -> dict:
        k = self.avetaar_db.avetaar_fetch_query("SELECT tax_rate, happiness, is_colony_of FROM avetaar_kingdoms WHERE chat_id = ?", (cid,))
        rate = k[0] if k else 30
        if evade:
            if random.random() < 0.3:
                self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET jail_time = ? WHERE user_id = ?", (time.time() + 3600, uid))
                return {"status": "caught", "net": 0, "tax": amount}
            else:
                self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET hidden_gold = hidden_gold + ? WHERE user_id = ?", (amount, uid))
                return {"status": "evaded", "net": amount, "tax": 0}
        tax = int(amount * (rate / 100))
        net = amount - tax
        self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET gold = gold + ? WHERE user_id = ?", (net, uid))
        if k:
            if k[2] != 0:
                tribute = int(tax * 0.1)
                self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury + ? WHERE chat_id = ?", (tax - tribute, cid))
                self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury + ? WHERE chat_id = ?", (tribute, k[2]))
            else:
                self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury + ? WHERE chat_id = ?", (tax, cid))
        return {"status": "paid", "net": net, "tax": tax, "rate": rate}

    def avetaar_mine(self, uid: int, cid: int, evade: bool = False) -> dict:
        u = self.avetaar_db.avetaar_fetch_query("SELECT * FROM avetaar_users WHERE user_id = ?", (uid,))
        k = self.avetaar_db.avetaar_fetch_query("SELECT siege_until, happiness FROM avetaar_kingdoms WHERE chat_id = ?", (cid,))
        now = time.time()
        if not u: return {"status": False, "msg": "<b>لم تسجل بعد</b>"}
        if u[22] > now: return {"status": False, "msg": "<b>انت في السجن بسبب التهرب الضريبي</b>"}
        if k and k[0] > now: return {"status": False, "msg": "<b>المملكة تحت الحصار لا يمكن التعدين</b>"}
        if u[15] == 1: return {"status": False, "msg": "<b>انت اسير حرب لا يمكنك العمل</b>"}
        if u[17] == 1: return {"status": False, "msg": "<b>انت مريض بالطاعون تحتاج لطبيب</b>"}
        if now - u[5] < 3600: return {"status": False, "msg": f"<b>عد بعد {int(3600 - (now - u[5]))} ثانية</b>"}
        hap_mod = (k[1] / 100) if k else 1.0
        base = random.randint(100, 500)
        mult = 1 + (u[4] * 0.01) + (u[10] * 0.05)
        if u[13] != 'لا يوجد': mult += 0.2
        if u[16] == 'لعنة': mult -= 0.3
        total = int(base * mult * hap_mod)
        res = self.avetaar_process_tax(uid, cid, total, evade)
        if res["status"] != "caught":
            title = self.avetaar_get_title(u[3]+res['net'], u[2]+50)
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET mine_count = mine_count + 1, last_mine = ?, total_xp = total_xp + 50, title = ? WHERE user_id = ?", (now, title, uid))
        self.avetaar_update_happiness(cid)
        return {"status": True, "data": res, "gross": total}

    def avetaar_cursed_mine(self, uid: int, cid: int) -> dict:
        if random.random() < 0.5:
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET gold = 0 WHERE user_id = ?", (uid,))
            return {"status": False, "msg": "<b>مت في المنجم الملعون وفقدت كل ذهبك</b>"}
        else:
            win = random.randint(5000, 15000)
            self.avetaar_process_tax(uid, cid, win)
            return {"status": True, "msg": f"<b>نجوت من اللعنة حصلت على {win} ذهبة</b>"}

    def avetaar_upgrade_weapon(self, uid: int, cid: int) -> str:
        u = self.avetaar_db.avetaar_fetch_query("SELECT gold FROM avetaar_users WHERE user_id = ?", (uid,))
        c = self.avetaar_db.avetaar_fetch_query("SELECT weapon_lvl FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, cid))
        if not c: return "<b>انت لست مواطنا هنا</b>"
        cost = (c[0] + 1) * 1000
        if u[0] < cost: return f"<b>تحتاج {cost} ذهبة لتطوير سلاحك</b>"
        self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET gold = gold - ? WHERE user_id = ?", (cost, uid))
        self.avetaar_db.avetaar_exec_query("UPDATE avetaar_citizens SET weapon_lvl = weapon_lvl + 1 WHERE user_id = ? AND chat_id = ?", (uid, cid))
        return f"<b>تم تطوير سلاحك الى مستوى {c[0]+1}</b>"

    def avetaar_war(self, atk_cid: int, def_kid: str) -> dict:
        def_k = self.avetaar_db.avetaar_fetch_query("SELECT * FROM avetaar_kingdoms WHERE kingdom_id = ?", (def_kid,))
        atk_k = self.avetaar_db.avetaar_fetch_query("SELECT * FROM avetaar_kingdoms WHERE chat_id = ?", (atk_cid,))
        if not def_k: return {"status": False, "msg": "<b>المملكة غير موجودة</b>"}
        if def_k[0] == atk_cid: return {"status": False, "msg": "<b>لا يمكن غزو نفسك</b>"}
        if def_k[11] == atk_cid or atk_k[11] == def_k[0]: return {"status": False, "msg": "<b>يوجد معاهدة سلام بينكم</b>"}
        now = time.time()
        if def_k[9] > now: return {"status": False, "msg": "<b>العدو يمتلك درع حماية</b>"}
        atk_army = self.avetaar_db.avetaar_fetch_all("SELECT COUNT(*) FROM avetaar_citizens WHERE chat_id = ?", (atk_cid,))[0][0]
        def_army = self.avetaar_db.avetaar_fetch_all("SELECT COUNT(*) FROM avetaar_citizens WHERE chat_id = ?", (def_k[0],))[0][0]
        atk_power = atk_army * random.randint(50, 150)
        def_power = def_army * random.randint(50, 150)
        if def_k[13] > now: def_power = int(def_power * 1.5)
        if atk_k[15] == 1: atk_power = int(atk_power * 0.5)
        if atk_power > def_power:
            loot = int(def_k[7] * 0.3)
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury - ? WHERE chat_id = ?", (loot, def_k[0]))
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury + ? WHERE chat_id = ?", (loot, atk_cid))
            pow_cits = self.avetaar_db.avetaar_fetch_all("SELECT user_id FROM avetaar_citizens WHERE chat_id = ? ORDER BY RANDOM() LIMIT 3", (def_k[0],))
            for p in pow_cits: self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET is_pow = 1 WHERE user_id = ?", (p[0],))
            return {"status": True, "msg": f"<b>نصر عظيم نهبت {loot} ذهبة واسرت جنودا</b>", "def_cid": def_k[0], "loot": loot}
        else:
            return {"status": False, "msg": "<b>هزيمة نكراء تحطمت جيوشكم</b>", "def_cid": def_k[0]}

    def avetaar_world_boss(self, uid: int, cid: int, dmg: int) -> str:
        g = self.avetaar_db.avetaar_fetch_query("SELECT boss_hp FROM avetaar_global WHERE id = 1")
        if g[0] <= 0: return "<b>لا يوجد وحش حاليا</b>"
        rem = g[0] - dmg
        if rem <= 0:
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_global SET boss_hp = 0 WHERE id = 1")
            self.avetaar_db.avetaar_exec_query("UPDATE avetaar_users SET gold = gold + 50000, title = 'قاهر الوحش' WHERE user_id = ?", (uid,))
            return "<b>قتلت وحش العالم وحصلت على 50,000 ذهبة</b>"
        self.avetaar_db.avetaar_exec_query("UPDATE avetaar_global SET boss_hp = ? WHERE id = 1", (rem,))
        return f"<b>ضربت الوحش تبقي له {rem} نقطة حياة</b>"

class AvetaarUltimateInterface:
    def __init__(self, token: str):
        self.token = token
        self.db = AvetaarUltimateDatabase()
        self.engine = AvetaarUltimateEngine(self.db)
        # حذف أي webhook عالق لضمان عمل polling
        try:
            requests.get(f"https://api.telegram.org/bot{token}/deleteWebhook", timeout=5)
        except:
            pass
        self.updater = Updater(token, use_context=True)

    def avetaar_kbd(self):
        return InlineKeyboardMarkup([[InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/TVXSSS")]])

    def avetaar_broadcast(self, context, msg: str):
        ks = self.db.avetaar_fetch_all("SELECT chat_id FROM avetaar_kingdoms")
        for k in ks:
            try: context.bot.send_message(k[0], msg, reply_markup=self.avetaar_kbd(), parse_mode="HTML")
            except: pass

    def avetaar_private_start(self, update: Update, context: CallbackContext):
        uid = update.effective_user.id
        self.db.avetaar_register_global(uid, update.effective_user.first_name)
        udata = self.db.avetaar_fetch_query("SELECT * FROM avetaar_users WHERE user_id = ?", (uid,))
        kname = "غير منتسب"
        if udata[6] != 0:
            kdata = self.db.avetaar_fetch_query("SELECT name FROM avetaar_kingdoms WHERE chat_id = ?", (udata[6],))
            if kdata: kname = kdata[0]
        btn = [[InlineKeyboardButton("اضف البوت لمملكتك", url=f"https://t.me/{context.bot.username}?startgroup=true")],[InlineKeyboardButton("𓄼𝗗𝗲𝘃𓄹", url="https://t.me/TVXSSS")]]
        m = (
            f"<b>نظام حرب الممالك العالمي</b>\n\nاهلا بك <code>{update.effective_user.first_name}</code>\n"
            f"تاريخ التسجيل: <code>{udata[7][:10]}</code>\nالمملكة الحالية: <code>{kname}</code>\n\n"
            f"<b>تعليمات</b>\n1. اضف البوت لمجموعتك\n2. يكتب المالك: تفعيل\n3. يكتب الاعضاء: ! تسجيل\n"
            f"4. لمعرفة الاوامر: ! الدستور"
        )
        update.message.reply_text(m, reply_markup=InlineKeyboardMarkup(btn), parse_mode="HTML")

    def avetaar_cmd_router(self, update: Update, context: CallbackContext):
        if not update.message or not update.message.text: return
        txt = update.message.text.strip()
        uid = update.effective_user.id
        cid = update.effective_chat.id
        
        if update.effective_chat.type not in ['group', 'supergroup']: return
        
        if txt in ["تفعيل", "ﺗﻔﻌﻴﻞ"]:
            m = context.bot.get_chat_member(cid, uid)
            if m.status == 'creator':
                kid = self.db.avetaar_init_kingdom(cid, update.effective_chat.title, uid)
                self.db.avetaar_exec_query("UPDATE avetaar_users SET current_kingdom = ? WHERE user_id = ?", (cid, uid))
                self.db.avetaar_exec_query("INSERT OR REPLACE INTO avetaar_citizens (user_id, chat_id, rank) VALUES (?, ?, 'امبراطور')", (uid, cid))
                update.message.reply_text(f"<b>تم تاسيس مملكة {update.effective_chat.title} | ID: {kid}</b>", reply_markup=self.avetaar_kbd(), parse_mode="HTML")
            return

        if not txt.startswith("!"): return
        self.db.avetaar_register_global(uid, update.effective_user.first_name)
        k = self.db.avetaar_fetch_query("SELECT * FROM avetaar_kingdoms WHERE chat_id = ?", (cid,))
        if not k: return

        parts = txt[1:].strip().split()
        if not parts: return
        
        cmd_1 = parts[0]
        cmd_2 = parts[0] + " " + parts[1] if len(parts) > 1 else ""
        
        two_word_cmds = ["تطوير سلاح", "سوق مظلم", "هجوم الوحش", "شراء مرافق", "منجم ملعون", "بناء عجيبة", "زواج سياسي"]
                         
        if cmd_2 in two_word_cmds:
            cmd = cmd_2
            args = parts[2:]
        else:
            cmd = cmd_1
            args = parts[1:]

        kbd = self.avetaar_kbd()

        # تسجيل
        if cmd in ["تسجيل", "ﺗﺴﺠﻴﻞ"]:
            cit = self.db.avetaar_fetch_query("SELECT * FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, cid))
            if cit:
                update.message.reply_text("<b>انت مسجل مسبقا</b>", reply_markup=kbd, parse_mode="HTML")
                return
            old_k = self.db.avetaar_fetch_query("SELECT current_kingdom FROM avetaar_users WHERE user_id = ?", (uid,))
            if old_k and old_k[0] != 0 and old_k[0] != cid:
                old_kdata = self.db.avetaar_fetch_query("SELECT kingdom_id, name FROM avetaar_kingdoms WHERE chat_id = ?", (old_k[0],))
                if old_kdata:
                    self.db.avetaar_log_traitor(old_kdata[0], update.effective_user.first_name, update.effective_chat.title)
                    self.db.avetaar_exec_query("DELETE FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, old_k[0]))
                    try: context.bot.send_message(old_k[0], f"<b>الخائن {update.effective_user.first_name} هرب الى {update.effective_chat.title}</b>", parse_mode="HTML")
                    except: pass
            self.db.avetaar_exec_query("UPDATE avetaar_users SET current_kingdom = ? WHERE user_id = ?", (cid, uid))
            self.db.avetaar_exec_query("INSERT INTO avetaar_citizens (user_id, chat_id) VALUES (?, ?)", (uid, cid))
            update.message.reply_text("<b>تم تجنيدك بنجاح</b>", reply_markup=kbd, parse_mode="HTML")

        # تعدين
        elif cmd in ["تعدين", "ﺗﻌﺪﻳﻦ"]:
            if not self.db.avetaar_fetch_query("SELECT * FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, cid)): return
            evade = len(args) > 0 and args[0] in ["تهرب", "ﺗﻬﺮﺏ"]
            res = self.engine.avetaar_mine(uid, cid, evade)
            if not res['status']:
                update.message.reply_text(res['msg'], reply_markup=kbd, parse_mode="HTML")
            else:
                d = res['data']
                if d['status'] == "caught":
                    m = f"<b>تم القبض عليك بتهمة التهرب الضريبي ومصادرة {d['tax']} ذهبة</b>"
                elif d['status'] == "evaded":
                    m = f"<b>تنقيب سري</b>\nاخفيت <code>{d['net']}</code> ذهبة بنجاح عن الضرائب"
                else:
                    m = f"<b>تنقيب</b>\nالربح: <code>{res['gross']}</code>\nالضريبة: <code>{d['tax']}</code>\nالصافي: <code>{d['net']}</code>"
                update.message.reply_text(m, reply_markup=kbd, parse_mode="HTML")

        # تطوير سلاح
        elif cmd in ["تطوير سلاح", "ﺗﻄﻮﻳﺮ ﺳﻼﺡ"]:
            msg = self.engine.avetaar_upgrade_weapon(uid, cid)
            update.message.reply_text(msg, reply_markup=kbd, parse_mode="HTML")

        # منجم ملعون
        elif cmd in ["منجم ملعون", "ﻣﻨﺠﻢ ﻣﻠﻌﻮﻥ"]:
            if not self.db.avetaar_fetch_query("SELECT * FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, cid)): return
            res = self.engine.avetaar_cursed_mine(uid, cid)
            update.message.reply_text(res['msg'], reply_markup=kbd, parse_mode="HTML")

        # حرب
        elif cmd in ["حرب", "ﺣﺮﺏ"]:
            if k[3] != uid: return
            if not args: return
            res = self.engine.avetaar_war(cid, args[0])
            update.message.reply_text(res['msg'], reply_markup=kbd, parse_mode="HTML")
            if res['status']:
                try: context.bot.send_message(res['def_cid'], f"<b>تم غزوكم من {k[2]} وسرقة {res['loot']} ذهب</b>", parse_mode="HTML")
                except: pass

        # وزير
        elif cmd in ["وزير", "ﻭﺯﻳﺮ"]:
            if k[3] != uid: return
            if len(args) < 1 or not update.message.reply_to_message: return
            tgt = update.message.reply_to_message.from_user.id
            t = args[0]
            if t in ["دفاع", "ﺩﻓﺎﻉ"]: self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET min_def = ? WHERE chat_id = ?", (tgt, cid))
            elif t in ["اقتصاد", "ﺍﻗﺘﺼﺎﺩ"]: self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET min_eco = ? WHERE chat_id = ?", (tgt, cid))
            elif t in ["داخلية", "ﺩﺍﺧﻠﻴﺔ"]: self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET min_int = ? WHERE chat_id = ?", (tgt, cid))
            update.message.reply_text(f"<b>تم تعيين الوزير بنجاح</b>", reply_markup=kbd, parse_mode="HTML")

        # انقلاب
        elif cmd in ["انقلاب", "ﺍﻧﻘﻼﺏ"]:
            if k[8] <= 70:
                update.message.reply_text("<b>الضريبة ليست ظالمة بما يكفي للانقلاب</b>", reply_markup=kbd, parse_mode="HTML")
                return
            new_emp = self.db.avetaar_fetch_query("SELECT user_id FROM avetaar_users WHERE current_kingdom = ? ORDER BY total_xp DESC LIMIT 1", (cid,))
            if new_emp:
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET emperor_id = ? WHERE chat_id = ?", (new_emp[0], cid))
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET tax_rate = 30 WHERE chat_id = ? ", (cid,))
                update.message.reply_text("<b>نجح الانقلاب تم اسقاط الامبراطور وارجاع الضريبة الى 30%</b>", reply_markup=kbd, parse_mode="HTML")

        # نفي
        elif cmd in ["نفي", "ﻧﻔﻲ"]:
            if k[3] != uid and k[6] != uid: return
            if not update.message.reply_to_message: return
            tgt = update.message.reply_to_message.from_user.id
            tgt_u = self.db.avetaar_fetch_query("SELECT gold FROM avetaar_users WHERE user_id = ?", (tgt,))
            if tgt_u:
                conf = int(tgt_u[0] * 0.5)
                self.db.avetaar_exec_query("UPDATE avetaar_users SET gold = gold - ?, current_kingdom = 0 WHERE user_id = ?", (conf, tgt))
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury + ? WHERE chat_id = ?", (conf, cid))
                self.db.avetaar_exec_query("DELETE FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (tgt, cid))
                update.message.reply_text(f"<b>تم نفي المواطن ومصادرة {conf} ذهب للخزينة</b>", reply_markup=kbd, parse_mode="HTML")

        # معاهدة
        elif cmd in ["معاهدة", "ﻣﻌﺎﻫﺪﺓ"]:
            if k[3] != uid: return
            if not args: return
            tgt_k = self.db.avetaar_fetch_query("SELECT chat_id FROM avetaar_kingdoms WHERE kingdom_id = ?", (args[0],))
            if tgt_k:
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET ally_id = ? WHERE chat_id = ?", (tgt_k[0], cid))
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET ally_id = ? WHERE chat_id = ?", (cid, tgt_k[0]))
                update.message.reply_text("<b>تم توقيع معاهدة السلام</b>", reply_markup=kbd, parse_mode="HTML")

        # جاسوس
        elif cmd in ["جاسوس", "ﺟﺎﺳﻮﺱ"]:
            if not args: return
            tgt_k = self.db.avetaar_fetch_query("SELECT chat_id FROM avetaar_kingdoms WHERE kingdom_id = ?", (args[0],))
            if tgt_k:
                self.db.avetaar_exec_query("UPDATE avetaar_citizens SET is_spy_for = ? WHERE user_id = ? AND chat_id = ?", (tgt_k[0], uid, cid))
                update.message.reply_text("<b>انت الان جاسوس سري</b>", reply_markup=kbd, parse_mode="HTML")

        # حصار
        elif cmd in ["حصار", "ﺣﺼﺎﺭ"]:
            if k[3] != uid and k[4] != uid: return
            if not args: return
            tgt_k = self.db.avetaar_fetch_query("SELECT chat_id FROM avetaar_kingdoms WHERE kingdom_id = ?", (args[0],))
            if tgt_k:
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET siege_until = ? WHERE chat_id = ?", (time.time() + 86400, tgt_k[0]))
                update.message.reply_text("<b>تم فرض الحصار لمدة 24 ساعة</b>", reply_markup=kbd, parse_mode="HTML")

        # فدية
        elif cmd in ["فدية", "ﻓﺪﻳﺔ"]:
            if not update.message.reply_to_message: return
            tgt = update.message.reply_to_message.from_user.id
            if k[7] >= 5000:
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury - 5000 WHERE chat_id = ?", (cid,))
                self.db.avetaar_exec_query("UPDATE avetaar_users SET is_pow = 0 WHERE user_id = ?", (tgt,))
                update.message.reply_text("<b>تم دفع الفدية وتحرير الاسير</b>", reply_markup=kbd, parse_mode="HTML")

        # مرتزقة
        elif cmd in ["مرتزقة", "ﻣﺮﺗﺰﻗﺔ"]:
            if k[3] != uid: return
            if k[7] >= 10000:
                self.db.avetaar_exec_query("UPDATE avetaar_kingdoms SET treasury = treasury - 10000, mercs_until = ? WHERE chat_id = ?", (time.time() + 172800, cid))
                update.message.reply_text("<b>تم شراء المرتزقة لحماية المملكة</b>", reply_markup=kbd, parse_mode="HTML")

        # هجوم الوحش
        elif cmd in ["هجوم الوحش", "ﻫﺠﻮﻡ ﺍﻟﻮﺣﺶ"]:
            res = self.engine.avetaar_world_boss(uid, cid, random.randint(500, 2000))
            update.message.reply_text(res, reply_markup=kbd, parse_mode="HTML")

        # مبارزة
        elif cmd in ["مبارزة", "ﻣﺒﺎﺭﺯﺓ"]:
            if not update.message.reply_to_message: return
            if random.random() > 0.5:
                self.db.avetaar_exec_query("UPDATE avetaar_users SET total_xp = total_xp + 100 WHERE user_id = ?", (uid,))
                update.message.reply_text("<b>انتصرت في الكولوسيوم</b>", reply_markup=kbd, parse_mode="HTML")
            else:
                update.message.reply_text("<b>هزمت في المبارزة</b>", reply_markup=kbd, parse_mode="HTML")

        # رصيدي
        elif cmd in ["رصيدي", "ﺭﺻﻴﺪﻱ"]:
            u = self.db.avetaar_fetch_query("SELECT gold FROM avetaar_users WHERE user_id = ?", (uid,))
            update.message.reply_text(f"<b>💰 رصيدك: {u[0]} ذهب</b>", reply_markup=kbd, parse_mode="HTML")

        # قواتي
        elif cmd in ["قواتي", "ﻗﻮﺍﺗﻲ"]:
            u_d = self.db.avetaar_fetch_query("SELECT * FROM avetaar_users WHERE user_id = ?", (uid,))
            c_d = self.db.avetaar_fetch_query("SELECT * FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (uid, cid))
            rank = c_d[2] if c_d else "عامة"
            m = (
                f"<b>ملف {u_d[1]}</b>\nالرتبة: <code>{rank}</code>\nاللقب: <code>{u_d[8]}</code>\n"
                f"الذهب: <code>{u_d[3]}</code>\nالمخبأ: <code>{u_d[12]}</code>\n"
                f"المرافق: <code>{u_d[13]}</code>\nالمهارات (هـ:{u_d[9]} ت:{u_d[10]} ف:{u_d[11]})"
            )
            update.message.reply_text(m, reply_markup=kbd, parse_mode="HTML")

        # المملكة
        elif cmd in ["المملكة", "ﺍﻟﻤﻤﻠﻜﺔ"]:
            m = (
                f"<b>بيانات الامبراطورية</b>\nالاسم: <code>{k[2]}</code>\nرمز ID: <code>{k[1]}</code>\n"
                f"الخزينة: <code>{k[7]}</code> 💰\nالضريبة: <code>{k[8]}%</code> 📉\n"
                f"السعادة: <code>{k[16]}%</code>"
            )
            update.message.reply_text(m, reply_markup=kbd, parse_mode="HTML")

        # رابطي
        elif cmd in ["رابطي", "ﺭﺍﺑﻄﻲ"]:
            try:
                link = context.bot.export_chat_invite_link(cid)
                update.message.reply_text(f"<b>رابط مملكتك:</b>\n{link}", reply_markup=kbd, parse_mode="HTML")
            except:
                update.message.reply_text("<b>يجب رفعي كمشرف</b>", reply_markup=kbd, parse_mode="HTML")

        # الدستور
        elif cmd in ["الدستور", "ﺍﻟﺪﺳﺘﻮﺭ"]:
            m = (
                f"<b>دستور مملكة Avetaar</b>\n"
                f"<code>! تسجيل</code> - <code>! تعدين [تهرب]</code> - <code>! منجم ملعون</code>\n"
                f"<code>! حرب [ID]</code> - <code>! وزير[دفاع/اقتصاد/داخلية]</code>\n"
                f"<code>! انقلاب</code> - <code>! نفي</code> - <code>! معاهدة [ID]</code>\n"
                f"<code>! جاسوس [ID]</code> - <code>! حصار [ID]</code> - <code>! فدية</code>\n"
                f"<code>! مرتزقة</code> - <code>! مستشفى</code> - <code>! سوق مظلم</code>\n"
                f"<code>! قرض</code> - <code>! قافلة [مبلغ]</code> - <code>! بورصة</code>\n"
                f"<code>! هجوم الوحش</code> - <code>! مبارزة</code> - <code>! تعويذة[درع/لعنة]</code>\n"
                f"<code>! شراء مرافق [اسم]</code> - <code>! تطوير[هجوم/تعدين]</code>\n"
                f"<code>! تطوير سلاح</code> - <code>! مخبأ [مبلغ]</code> - <code>! مهامي</code>\n"
                f"<code>! محكمة</code> - <code>! اندماج [ID]</code> - <code>! ضريبة [1-100]</code>\n"
                f"<code>! اغتيال</code> - <code>! مكافأة [مبلغ]</code> - <code>! ايداع [مبلغ]</code>\n"
                f"<code>! سحب [مبلغ]</code> - <code>! تخريب [ID]</code> - <code>! استعمار [ID]</code>\n"
                f"<code>! ابتزاز</code> - <code>! دعاية</code> - <code>! بناء عجيبة</code>\n"
                f"<code>! طبيب</code> - <code>! زواج سياسي [ID]</code>\n"
                f"<code>! قواتي</code> - <code>! المملكة</code> - <code>! رصيدي</code> - <code>! رابطي</code>"
            )
            update.message.reply_text(m, reply_markup=kbd, parse_mode="HTML")

    def avetaar_leave_monitor(self, update: Update, context: CallbackContext):
        res = update.chat_member
        if not res: return
        if res.new_chat_member.status in ['left', 'kicked']:
            self.db.avetaar_exec_query("DELETE FROM avetaar_citizens WHERE user_id = ? AND chat_id = ?", (res.old_chat_member.user.id, res.chat.id))

    def avetaar_ignite(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("start", self.avetaar_private_start, filters=Filters.private))
        dp.add_handler(MessageHandler(Filters.group & Filters.text, self.avetaar_cmd_router))
        dp.add_handler(ChatMemberHandler(self.avetaar_leave_monitor, ChatMemberHandler.CHAT_MEMBER))
        self.updater.start_polling()
        self.updater.idle()
        print("✅ البوت يعمل")

if __name__ == "__main__":
    print("🚀 جاري تشغيل بوت حرب الممالك...")
    # حذف webhook قبل بدء التشغيل
    try:
        requests.get(f"https://api.telegram.org/bot{avetaar_token}/deleteWebhook", timeout=5)
    except:
        pass
    bot = AvetaarUltimateInterface(avetaar_token)
    bot.avetaar_ignite()