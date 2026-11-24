import sqlite3, telebot, requests, kvsqlite, time, datetime
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlite3 import Error

dat = kvsqlite.sync.Client('users.sqlite', 'users')

def daily(userid):
    user_data = dat.get(f'user_try_{userid}')
    if not user_data:
        user_data = {'points': 50, 'last_update': int(time.time())}
        dat.set(f'user_try_{userid}', (user_data))
        return {'status': True, 'points': 50}
    else:
        last_update_time = datetime.datetime.fromtimestamp(user_data['last_update'])
        time_since_last_update = datetime.datetime.now() - last_update_time
        if time_since_last_update.total_seconds() >= 86400:
            user_data['points'] = 50
            user_data['last_update'] = int(time.time())
            dat.set(f'user_try_{userid}', (user_data))
            return {'status': True, 'points': 50}
        else:
            return {'status':False, 'points': user_data['points']}

def open_db(name):
    try:
        db = sqlite3.connect(f"{name}.sqlite")
        db.execute('PRAGMA journal_mode=WAL')
        return db
    except Error as e:
        print(e)

def get_table_name(db):
    try:
        cur = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        row = cur.fetchone()
        return row[0] if row else 'person'
    except:
        return 'person'

def fam(db, id):
    table = get_table_name(db)
    # جلب 18 حقلاً
    query = f'''SELECT 
        p_first, p_father, p_grand, p_birth, 
        f_house, f_street, f_area, f_dist, 
        p_mother, gr_mother, p_job, t_job, 
        p_case, p_isudt, soc, rc_name, 
        mark, fam_no
        FROM "{table}" WHERE fam_no = ?'''
    
    x = db.execute(query, [id])
    names = []
    for i in x:
        try:
            birth = int(i[3]) / 100
            names.append({
                'p_first': i[0], 'p_father': i[1], 'p_grand': i[2], 'birth': f'{int(birth)}',
                'house': i[4] if i[4] else 'غير مسجل', 'street': i[5] if i[5] else 'غير مسجل',
                'area': i[6] if i[6] else 'غير مسجل', 'dist': i[7] if i[7] else 'غير مسجل',
                'mother': i[8] if i[8] else 'غير مسجل', 'gr_mother': i[9] if i[9] else 'غير مسجل',
                'job': i[10] if i[10] else 'غير مسجل', 't_job': i[11] if i[11] else 'غير مسجل',
                'case': i[12] if i[12] else 'غير مسجل', 'isudt': i[13] if i[13] else 'غير مسجل',
                'soc': i[14] if i[14] else 'غير مسجل', 'rc_name': i[15] if i[15] else 'غير مسجل',
                'mark': i[16] if i[16] else 'غير مسجل', 'fam_no': i[17]
            })
        except:
            continue
    return names

token = '8824567350:AAFozC5yVrG6E10XMBk-GcCyskQtL9AkzLw'
bot = telebot.TeleBot(token, num_threads=20, skip_pending=True)

telebot.apihelper.proxy = {'https': 'socks5h://127.0.0.1:9050'}

adds = [865508765]

if not dat.exists("ban"):
    dat.set("ban", [])

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, 'ارسل اسمين أو ثلاثة فقط:\nمثال: محمد شامي')

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id in dat.get("ban"): return
    if not dat.exists(f"user_{message.from_user.id}"):
        dat.set(f"user_{message.from_user.id}", {'id':message.from_user.id, 'paid':False, 'try':5})
    x = daily(message.from_user.id)
    if int(x['points']) < 1:
        bot.reply_to(message, 'عذرا صديقي، محاولاتك خلصت.')
        return
    points = x['points']
    key = InlineKeyboardMarkup(row_width=2)
    a1 = types.InlineKeyboardButton(text="- اربيل",callback_data="ar")
    a2 = types.InlineKeyboardButton(text="- الانبار",callback_data="an")
    a3 = types.InlineKeyboardButton(text="- النجف",callback_data="n")
    a4 = types.InlineKeyboardButton(text="- بابل",callback_data="ba")
    a5 = types.InlineKeyboardButton(text="- البصرة",callback_data="bs")
    a6 = types.InlineKeyboardButton(text="- دهوك",callback_data="dh")
    a7 = types.InlineKeyboardButton(text="- ديالى",callback_data="dy")
    a8 = types.InlineKeyboardButton(text="- ذي قار",callback_data="zy")
    a9 = types.InlineKeyboardButton(text="- سليمانية",callback_data="sl")
    a10 = types.InlineKeyboardButton(text="- صلاح الدين",callback_data="sa")
    a11 = types.InlineKeyboardButton(text="- القادسية",callback_data="qa")
    a12 = types.InlineKeyboardButton(text="- كربلاء",callback_data="kr")
    a13 = types.InlineKeyboardButton(text="- كركوك",callback_data="ko")
    a14 = types.InlineKeyboardButton(text="- المثنى",callback_data="mu")
    a15 = types.InlineKeyboardButton(text="- ميسان",callback_data="mes")
    a16 = types.InlineKeyboardButton(text="- نينوى",callback_data="ny")
    a17 = types.InlineKeyboardButton(text="- واسط",callback_data="wa")
    a18 = types.InlineKeyboardButton(text="- بغداد",callback_data="bag")
    a19 = types.InlineKeyboardButton(text="- بلد",callback_data="bld")
    key.add(a17,a16,a15,a14,a13,a12,a11,a10,a9,a8,a7,a6,a5,a4,a3,a2,a1,a18, a19)
    bot.reply_to(message, f'اهلا بيك ببوت البيانات ..\nمحاولاتك: {points}', reply_markup=key)

@bot.callback_query_handler(func=lambda m:True)
def qu(call):
    x = daily(call.from_user.id)
    if int(x['points']) < 1:
        bot.reply_to(call.message, 'عذرا صديقي، محاولاتك خلصت.')
        return
    if call.data.startswith("get:"):
        bot.send_message(call.message.chat.id, 'انتظر، جاري جلب العائلة ..')
        famid = call.data.split(':')[1]
        place = call.data.split(":")[2]
        d = open_db(place)
        if not d:
            bot.send_message(call.message.chat.id, f'ملف {place}.sqlite غير موجود.')
            return
        fams = fam(d, famid)
        if len(fams) > 0:
            for i in fams:
                now = int(datetime.datetime.now().year) - int(i['birth'])
                
                k = f'''الاسم: {i['p_first']} {i['p_father']} {i['p_grand']}
المواليد: {i['birth']}
العمر: {now}
البطاقة التموينية: {i['fam_no']}
المنطقة/الناحية: {i['area']}
القضاء: {i['dist']}
الزقاق/الشارع: {i['street']}
رقم الدار: {i['house']}
اسم الأم: {i['mother']}
اسم الجدة: {i['gr_mother']}
المهنة: {i['job']}
نوع العمل: {i['t_job']}
الحالة: {i['case']}
حالة التحديث: {i['isudt']}
الرقم الاجتماعي: {i['soc']}
مركز التسجيل: {i['rc_name']}
ملاحظات: {i['mark']}
المحافظة: {place}'''
                
                bot.send_message(call.message.chat.id, k)
                
            if dat.get(f'user_{call.from_user.id}')['paid']:
                bot.reply_to(call.message, 'تمت بنجاح')
            else:
                if not dat.get(f'user_try_{call.from_user.id}'):
                    dat.set(f'user_try_{call.from_user.id}', {'points':7,'last_update': int(time.time())})
                else:
                    user_try = (dat.get(f'user_try_{call.from_user.id}'))
                    user_try['points'] -= 1
                    dat.set(f'user_try_{call.from_user.id}', user_try)
                    bot.reply_to(call.message, 'تمت بنجاح')
        d.close()
        return

    places = {'ar': 'اربيل', 'an': 'الانبار', 'n': 'النجف الاشرف', 'ba': 'بابل', 'bs': 'بصرة', 'dh': 'دهوك', 'dy': 'ديالى', 'zy': 'ذي قار', 'sl': 'سليمانية', 'sa': 'صلاح الدين', 'qa': 'قادسية', 'kr': 'كربلاء المقدسة', 'ko': 'كركوك', 'mu': 'مثنى', 'mes': 'ميسان', 'ny': 'نينوى', 'wa': 'واسط', 'bag': 'بغداد', 'bld': 'بلد'}
    if call.data in places:
        place = places[call.data]
        h = bot.send_message(call.message.chat.id, f'{place} - دزلي اسمين أو ثلاثة فقط | مثال: محمد شامي')
        bot.register_next_step_handler(h, search, place)

def search(message, place):
    namer = message.text.strip()
    parts = namer.split()
    if len(parts) not in (2, 3):
        bot.reply_to(message, 'ارسل اسمين أو ثلاثة فقط. مثال: محمد شامي')
        return
    o = bot.reply_to(message, 'انتظر شوي ..')
    d = open_db(place)
    if not d:
        bot.reply_to(message, 'عذرا، ملف قاعدة البيانات غير موجود.')
        return
    table = get_table_name(d)
    first_name = parts[0]
    father_name = parts[1] if len(parts) >= 2 else ''
    grand_name = parts[2] if len(parts) == 3 else ''

    where = f"p_first LIKE '{first_name}%'"
    if father_name: where += f" AND p_father LIKE '{father_name}%'"
    if grand_name: where += f" AND p_grand LIKE '{grand_name}%'"

    query = f"SELECT fam_no, p_first, p_father, p_grand, p_birth FROM \"{table}\" WHERE {where} LIMIT 30"
    try:
        rows = d.execute(query).fetchall()
    except Exception as e:
        bot.reply_to(message, f'خطأ في القاعدة: {e}')
        d.close()
        return

    if len(rows) > 0:
        for row in rows:
            try:
                fam = row[0]
                fname, mname, lname = row[1], row[2], row[3]
                try: birth = int(int(row[4]) / 100)
                except: birth = row[4]
                n = f'{fname} {mname} {lname}'.replace("\x84", "")
                m = InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('جلب العائلة .', callback_data=f'get:{fam}:{place}'))
                
                bot.send_message(message.chat.id, f'الاسم: {n} .\nالمواليد: {birth}\nرقم العائلة: {fam}\nالمحافظة: {place}', reply_markup=m)
                
                time.sleep(0.2)
            except Exception as e:
                print(e)
        d.close()
    else:
        bot.reply_to(message, 'ما لكيت اي اسم ..')
        d.close()

print("البوت يعمل الآن ...")
while True:
    try:
        bot.infinity_polling(skip_pending=True, timeout=30)
    except Exception as e:
        print(f"انقطع الاتصال، إعادة المحاولة...")
        time.sleep(5)
