#!/usr/bin/env python3
import os
import sys
import subprocess
import threading
import time
import shutil
import zipfile
import tarfile
import sqlite3
import signal
import ast
import importlib
import importlib.util
import html as html_lib
import logging
import json
import re
from datetime import datetime, timedelta
import requests

# ----------------------------------------------------
# SMALL CAPS CONVERTER UTILITY
# ----------------------------------------------------
SMALL_CAPS_MAP = {
    'a': '𝚊',
    'b': '𝚋',
    'c': '𝚌',
    'd': '𝚍',
    'e': '𝚎',
    'f': '𝚏',
    'g': '𝚐',
    'h': '𝚑',
    'i': '𝚒',
    'j': '𝚓',
    'k': '𝚔',
    'l': '𝚕',
    'm': '𝚖',
    'n': '𝚗',
    'o': '𝚘',
    'p': '𝚙',
    'q': '𝚚',
    'r': '𝚛',
    's': '𝚜',
    't': '𝚝',
    'u': '𝚞',
    'v': '𝚟',
    'w': '𝚠',
    'x': '𝚡',
    'y': '𝚢',
    'z': '𝚣',
    'A': '𝙰',
    'B': '𝙱',
    'C': '𝙲',
    'D': '𝙳',
    'E': '𝙴',
    'F': '𝙵',
    'G': '𝙶',
    'H': '𝙷',
    'I': '𝙸',
    'J': '𝙹',
    'K': '𝙺',
    'L': '𝙻',
    'M': '𝙼',
    'N': '𝙽',
    'O': '𝙾',
    'P': '𝙿',
    'Q': '𝚀',
    'R': '𝚁',
    'S': '𝚂',
    'T': '𝚃',
    'U': '𝚄',
    'V': '𝚅',
    'W': '𝚆',
    'X': '𝚇',
    'Y': '𝚈',
    'Z': '𝚉',
}

def to_small_caps(text: str) -> str:
    """Converts alphabetic characters to small caps while preserving emojis and special characters."""
    return "".join(SMALL_CAPS_MAP.get(c, c) for c in text)

# ----------------------------------------------------
# AUTO INSTALL BASE DEPENDENCIES
# ----------------------------------------------------
def install_requirements():
    requirements = [
        "pyTelegramBotAPI",
        "requests", 
        "psutil",
        "flask",
        "aiohttp",
        "aiogram",
        "nest_asyncio"
    ]
    for package in requirements:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", package], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

install_requirements()

import psutil
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from flask import Flask

# ----------------------------------------------------
# RENDER WEB SERVICE PORT BINDING (BACKGROUND HTTP)
# ----------------------------------------------------
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ 𝙲𝚁𝙰𝙲𝙺 CODEX HOSTING CORE IS OPERATIONAL 24/7 🚀"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ----------------------------------------------------
# BOT CONFIGURATION
# ----------------------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8719242113:AAFpTn9FNI0i0dzKiks-eav0AnmCFBVwC0g")
OWNER_ID = int(os.environ.get("OWNER_ID", 5628671567))
ADMIN_ID = int(os.environ.get("ADMIN_ID", 5628671567))
YOUR_USERNAME = '@Xalonexdev03'
UPDATE_CHANNEL = 'https://t.me/pdf_making_hub'

POWERED_BY_TEXT = "𝚙𝚘𝚠𝚎𝚛𝚎𝚍 𝚋𝚢 @CRACK_CoDeX"

CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", "95.0"))
MEMORY_THRESHOLD = float(os.environ.get("MEMORY_THRESHOLD", "95.0"))
MAX_RUNNING_PROCESSES = int(os.environ.get("MAX_RUNNING_PROCESSES", "30"))
MAX_FILES_PER_USER = int(os.environ.get("MAX_FILES_PER_USER", "25"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "metadata.db")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
LOGS_DIR = os.path.join(DATA_DIR, "logs")
TEMP_DIR = os.path.join(DATA_DIR, "temp")

for directory in [DATA_DIR, UPLOADS_DIR, LOGS_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

START_TIME = datetime.utcnow()
BOT_START_TIME = datetime.now()

def get_uptime():
    uptime = datetime.now() - BOT_START_TIME
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{days}ᴅ {hours}ʜ {minutes}ᴍ {seconds}ꜱ"

# ----------------------------------------------------
# DATABASE
# ----------------------------------------------------
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.row_factory = sqlite3.Row
db_lock = threading.Lock()

def init_db():
    with db_lock:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, username TEXT, filename TEXT, orig_name TEXT,
            path TEXT, uploaded_at TEXT, file_type TEXT, pid INTEGER, status TEXT DEFAULT 'Stopped'
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id INTEGER, started_at TEXT, finished_at TEXT,
            pid INTEGER, log_path TEXT, exit_code INTEGER
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY, username TEXT, joined_at TEXT, last_seen TEXT
        )''')
        cur.execute('''CREATE TABLE IF NOT EXISTS subscriptions (user_id INTEGER PRIMARY KEY, expiry TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS admins (user_id INTEGER PRIMARY KEY)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS banned_users (user_id INTEGER PRIMARY KEY, reason TEXT, banned_by INTEGER, banned_at TEXT)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER, file_id INTEGER, PRIMARY KEY (user_id, file_id))''')
        cur.execute('''CREATE TABLE IF NOT EXISTS bot_stats (stat_name TEXT PRIMARY KEY, stat_value INTEGER DEFAULT 0)''')
        cur.execute('''CREATE TABLE IF NOT EXISTS user_limits (user_id INTEGER PRIMARY KEY, file_limit INTEGER)''')
        
        cur.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (OWNER_ID,))
        if ADMIN_ID != OWNER_ID:
            cur.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (ADMIN_ID,))
        
        for stat in ['total_uploads', 'total_downloads', 'total_runs']:
            cur.execute('INSERT OR IGNORE INTO bot_stats (stat_name, stat_value) VALUES (?, 0)', (stat,))
        conn.commit()

init_db()

def add_file_record(user_id, username, filename, orig_name, path, file_type):
    with db_lock:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO files (user_id, username, filename, orig_name, path, uploaded_at, file_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, filename, orig_name, path, datetime.utcnow().isoformat(), file_type)
        )
        conn.commit()
        return cur.lastrowid

def list_user_files(user_id):
    cur = conn.cursor()
    cur.execute("SELECT id, filename, orig_name, uploaded_at, file_type, status, pid FROM files WHERE user_id=? ORDER BY id DESC", (user_id,))
    return cur.fetchall()

def get_file_record(file_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM files WHERE id=?", (file_id,))
    return cur.fetchone()

def remove_file_record(file_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute("DELETE FROM files WHERE id=?", (file_id,))
        conn.commit()

def record_run_start(file_id, pid, log_path):
    with db_lock:
        cur = conn.cursor()
        cur.execute("INSERT INTO runs (file_id, started_at, pid, log_path) VALUES (?, ?, ?, ?)",
                    (file_id, datetime.utcnow().isoformat(), pid, log_path))
        conn.commit()
        return cur.lastrowid

def record_run_finish(run_id, exit_code):
    with db_lock:
        cur = conn.cursor()
        cur.execute("UPDATE runs SET finished_at=?, exit_code=? WHERE id=?", (datetime.utcnow().isoformat(), exit_code, run_id))
        conn.commit()

def update_file_status(file_id, pid, status):
    with db_lock:
        cur = conn.cursor()
        cur.execute("UPDATE files SET pid=?, status=? WHERE id=?", (pid, status, file_id))
        conn.commit()

def save_subscription(user_id, expiry):
    with db_lock:
        cur = conn.cursor()
        cur.execute('INSERT OR REPLACE INTO subscriptions (user_id, expiry) VALUES (?, ?)', (user_id, expiry.isoformat()))
        conn.commit()

def remove_subscription(user_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
        conn.commit()

def get_subscription(user_id):
    cur = conn.cursor()
    cur.execute('SELECT expiry FROM subscriptions WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if row:
        return datetime.fromisoformat(row[0])
    return None

def add_admin(user_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute('INSERT OR IGNORE INTO admins (user_id) VALUES (?)', (user_id,))
        conn.commit()
        admin_ids.add(user_id)

def remove_admin_db(user_id):
    if user_id == OWNER_ID:
        return False
    with db_lock:
        cur = conn.cursor()
        cur.execute('DELETE FROM admins WHERE user_id = ?', (user_id,))
        conn.commit()
        admin_ids.discard(user_id)
        return True

def ban_user(user_id, reason, banned_by):
    with db_lock:
        cur = conn.cursor()
        cur.execute('INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, banned_at) VALUES (?, ?, ?, ?)',
                    (user_id, reason, banned_by, datetime.utcnow().isoformat()))
        conn.commit()
        banned_users.add(user_id)

def unban_user(user_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute('DELETE FROM banned_users WHERE user_id = ?', (user_id,))
        conn.commit()
        banned_users.discard(user_id)

def is_user_banned(user_id):
    return user_id in banned_users

def toggle_favorite(user_id, file_id):
    with db_lock:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM favorites WHERE user_id = ? AND file_id = ?', (user_id, file_id))
        exists = cur.fetchone()
        if exists:
            cur.execute('DELETE FROM favorites WHERE user_id = ? AND file_id = ?', (user_id, file_id))
            return False
        else:
            cur.execute('INSERT INTO favorites (user_id, file_id) VALUES (?, ?)', (user_id, file_id))
            return True

def get_favorites(user_id):
    cur = conn.cursor()
    cur.execute('SELECT file_id FROM favorites WHERE user_id = ?', (user_id,))
    return [row[0] for row in cur.fetchall()]

processes = {}
proc_lock = threading.Lock()
admin_ids = {ADMIN_ID, OWNER_ID}
banned_users = set()
bot_locked = False
user_subscriptions = {}

def load_data():
    global user_subscriptions, banned_users, admin_ids
    try:
        cur = conn.cursor()
        cur.execute('SELECT user_id, expiry FROM subscriptions')
        for user_id, expiry in cur.fetchall():
            try:
                user_subscriptions[user_id] = {'expiry': datetime.fromisoformat(expiry)}
            except Exception:
                pass
        cur.execute('SELECT user_id FROM banned_users')
        banned_users.update(row[0] for row in cur.fetchall())
        cur.execute('SELECT user_id FROM admins')
        admin_ids.update(row[0] for row in cur.fetchall())
    except Exception as e:
        logger.error(f"Error loading data: {e}")

load_data()

def get_system_load():
    try:
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        proc_count = len(processes)
        return float(cpu), float(mem), int(proc_count)
    except Exception:
        return 0.0, 0.0, 0

def should_stop_due_to_load():
    load, memory, process_count = get_system_load()
    if process_count >= MAX_RUNNING_PROCESSES:
        return True, to_small_caps(f"Too many running processes ({process_count}/{MAX_RUNNING_PROCESSES})")
    if load >= CPU_THRESHOLD:
        return True, to_small_caps(f"High CPU load ({load}%)")
    if memory >= MEMORY_THRESHOLD:
        return True, to_small_caps(f"High memory usage ({memory}%)")
    return False, None

def get_user_file_limit(user_id):
    if user_id == OWNER_ID: return float('inf')
    if user_id in admin_ids: return 999
    if user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now():
        return 50
    cur = conn.cursor()
    cur.execute("SELECT file_limit FROM user_limits WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row: return row[0]
    return MAX_FILES_PER_USER

def get_file_type(filename):
    if not filename: return "unknown"
    name = filename.lower()
    if name.endswith(".py"): return "python"
    if name.endswith(".js"): return "javascript"
    if name.endswith(".zip"): return "zip"
    if any(name.endswith(ext) for ext in [".tar", ".tar.gz", ".tgz"]): return "archive"
    return "unknown"

def extract_archive(file_path, extract_dir):
    try:
        if file_path.lower().endswith(".zip"):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif any(file_path.lower().endswith(x) for x in [".tar.gz", ".tgz", ".tar"]):
            with tarfile.open(file_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_dir)
        else:
            return False, "Unsupported archive format"
        return True, None
    except Exception as e:
        return False, str(e)

def find_main_file(directory):
    priority_files = [
        "main.py", "bot.py", "app.py", "server.py", "index.py", "run.py", "core.py",
        "main.js", "bot.js", "app.js", "server.js", "index.js"
    ]
    for file_name in priority_files:
        file_path = os.path.join(directory, file_name)
        if os.path.isfile(file_path):
            return file_path
    for root, dirs, files in os.walk(directory):
        for file_name in priority_files:
            if file_name in files:
                return os.path.join(root, file_name)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py") or file.endswith(".js"):
                return os.path.join(root, file)
    return None

def install_requirements_from_file(requirements_path):
    try:
        if not os.path.exists(requirements_path):
            return False, "requirements.txt not found"
        with open(requirements_path, 'r') as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        if not requirements:
            return True, "No packages in requirements.txt"
        
        failed = []
        for pkg in requirements:
            res = subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True, text=True, timeout=180)
            if res.returncode != 0:
                failed.append(pkg)
        if failed:
            return False, f"Failed installing: {', '.join(failed[:4])}"
        return True, "All requirements installed successfully"
    except Exception as e:
        return False, str(e)

def extract_imports(file_path):
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    imports.add(node.module.split('.')[0])
    except Exception:
        pass
    return imports

def install_missing_imports(imports):
    missing = []
    for module in imports:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)
    if not missing:
        return True, "All modules available"
    
    pip_name_map = {
        'telebot': 'pyTelegramBotAPI', 'PIL': 'Pillow', 'cv2': 'opencv-python',
        'Crypto': 'pycryptodome', 'bs4': 'beautifulsoup4', 'aiohttp': 'aiohttp',
        'aiogram': 'aiogram', 'pyrogram': 'pyrogram', 'tgcrypto': 'tgcrypto'
    }
    for module in missing:
        pkg = pip_name_map.get(module, module)
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg], capture_output=True, text=True, timeout=120)
        except Exception:
            pass
    return True, "Import dependencies resolved"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ----------------------------------------------------
# UI KEYBOARDS (ALL LABELS IN SMALL CAPS)
# ----------------------------------------------------
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton(f"📢 {to_small_caps('Updates Channel')}"), KeyboardButton(f"⏱ {to_small_caps('Uptime')}"))
    kb.add(KeyboardButton(f"📤 {to_small_caps('Upload File')}"), KeyboardButton(f"📁 {to_small_caps('My Files')}"))
    kb.add(KeyboardButton(f"⭐ {to_small_caps('Favorites')}"), KeyboardButton(f"🔍 {to_small_caps('Search Files')}"))
    kb.add(KeyboardButton(f"⚡ {to_small_caps('Bot Speed')}"), KeyboardButton(f"📊 {to_small_caps('Statistics')}"))
    kb.add(KeyboardButton(f"📞 {to_small_caps('Contact Owner')}"), KeyboardButton(f"🤖 {to_small_caps('MPX AI')}"))
    kb.add(KeyboardButton(f"📦 {to_small_caps('Manual Install')}"), KeyboardButton(f"🆘 {to_small_caps('Help')}"))
    return kb

def admin_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(KeyboardButton(f"📢 {to_small_caps('Updates Channel')}"), KeyboardButton(f"⏱ {to_small_caps('Uptime')}"))
    kb.add(KeyboardButton(f"📤 {to_small_caps('Upload File')}"), KeyboardButton(f"📁 {to_small_caps('My Files')}"))
    kb.add(KeyboardButton(f"⭐ {to_small_caps('Favorites')}"), KeyboardButton(f"🔍 {to_small_caps('Search Files')}"))
    kb.add(KeyboardButton(f"⚡ {to_small_caps('Bot Speed')}"), KeyboardButton(f"📊 {to_small_caps('Statistics')}"))
    kb.add(KeyboardButton(f"💳 {to_small_caps('Subscriptions')}"), KeyboardButton(f"📢 {to_small_caps('Broadcast')}"))
    kb.add(KeyboardButton(f"🔒 {to_small_caps('Lock Bot')}"), KeyboardButton(f"🟢 {to_small_caps('Run All Files')}"))
    kb.add(KeyboardButton(f"👑 {to_small_caps('Admin Panel')}"), KeyboardButton(f"📞 {to_small_caps('Contact Owner')}"))
    kb.add(KeyboardButton(f"🤖 {to_small_caps('MPX AI')}"), KeyboardButton(f"📦 {to_small_caps('Manual Install')}"))
    kb.add(KeyboardButton(f"👥 {to_small_caps('User Management')}"), KeyboardButton(f"🛠️ {to_small_caps('Admin Install')}"))
    return kb

def file_actions_kb(file_id, is_running=False):
    kb = InlineKeyboardMarkup()
    if is_running:
        kb.row(
            InlineKeyboardButton(f"⏹ {to_small_caps('Stop')}", callback_data=f"stop:{file_id}"),
            InlineKeyboardButton(f"🔁 {to_small_caps('Restart')}", callback_data=f"restart:{file_id}")
        )
    else:
        kb.row(
            InlineKeyboardButton(f"▶️ {to_small_caps('Start')}", callback_data=f"start:{file_id}"),
            InlineKeyboardButton(f"🔁 {to_small_caps('Restart')}", callback_data=f"restart:{file_id}")
        )
    kb.row(
        InlineKeyboardButton(f"⭐ {to_small_caps('Favorite')}", callback_data=f"fav:{file_id}"),
        InlineKeyboardButton(f"🗑 {to_small_caps('Delete')}", callback_data=f"delete:{file_id}")
    )
    kb.row(
        InlineKeyboardButton(f"📄 {to_small_caps('Logs')}", callback_data=f"logs:{file_id}"),
        InlineKeyboardButton(f"📥 {to_small_caps('Download')}", callback_data=f"download:{file_id}")
    )
    kb.row(InlineKeyboardButton(f"⬅️ {to_small_caps('Back to Files')}", callback_data="back_to_files"))
    return kb

def admin_panel_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.row(
        InlineKeyboardButton(f"👥 {to_small_caps('User Stats')}", callback_data="admin_total_users"),
        InlineKeyboardButton(f"📁 {to_small_caps('Files Stats')}", callback_data="admin_total_files")
    )
    kb.row(
        InlineKeyboardButton(f"🚀 {to_small_caps('Running Scripts')}", callback_data="admin_running_scripts"),
        InlineKeyboardButton(f"💎 {to_small_caps('Premium Users')}", callback_data="admin_premium_users")
    )
    kb.row(
        InlineKeyboardButton(f"➕ {to_small_caps('Add Admin')}", callback_data="admin_add_admin"),
        InlineKeyboardButton(f"➖ {to_small_caps('Remove Admin')}", callback_data="admin_remove_admin")
    )
    kb.row(
        InlineKeyboardButton(f"📊 {to_small_caps('System Analytics')}", callback_data="admin_system_status"),
        InlineKeyboardButton(f"💾 {to_small_caps('Backup Database')}", callback_data="admin_backup_db")
    )
    kb.row(
        InlineKeyboardButton(f"🗑️ {to_small_caps('Clean Logs')}", callback_data="admin_clean_files"),
        InlineKeyboardButton(f"🔄 {to_small_caps('Restart Bot')}", callback_data="admin_restart_bot")
    )
    kb.row(InlineKeyboardButton(f"🏠 {to_small_caps('Main Menu')}", callback_data="back_to_main"))
    return kb

# ----------------------------------------------------
# COMMAND HANDLERS
# ----------------------------------------------------
@bot.message_handler(commands=['start', 'help'])
def start_handler(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.reply_to(message, f"🚫 {to_small_caps('You are banned from using this bot!')}\n\n🏷️ {POWERED_BY_TEXT}")
        return
    
    with db_lock:
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO users (user_id, username, joined_at, last_seen) VALUES (?, ?, ?, ?)",
            (user_id, message.from_user.username or "", datetime.utcnow().isoformat(), datetime.utcnow().isoformat())
        )
        conn.commit()

    is_premium = user_id in user_subscriptions and user_subscriptions[user_id]['expiry'] > datetime.now()
    role_badge = "👑 𝙰𝙳𝙼𝙸𝙽" if user_id in admin_ids else ("💎 𝙿𝚁𝙴𝙼𝙸𝚄𝙼" if is_premium else "🆓 𝙵𝚁𝙴𝙴")
    
    welcome_text = f"""
🚀 <b>{to_small_caps('𝙲𝚁𝙰𝙲𝙺 CODEX CLOUD HOSTING CORE')}</b> ☠️
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>{to_small_caps('User ID')}:</b> <code>{user_id}</code>
🔰 <b>{to_small_caps('Account Tier')}:</b> {role_badge}
━━━━━━━━━━━━━━━━━━━━━━━
🌟 <b>{to_small_caps('Supported Architectures & Frameworks')}:</b>
🐍 <b>{to_small_caps('Python Engines')}</b> (.ᴘʏ, ᴀɪᴏɢʀᴀᴍ, ᴀɪᴏʜᴛᴛᴘ, ᴘʏʀᴏɢʀᴀᴍ)
🟨 <b>{to_small_caps('Node.js Engines')}</b> (.ᴊꜱ, ᴇxᴘʀᴇꜱꜱ, ᴡꜱ)
🎮 <b>{to_small_caps('Gaming Sockets')}</b> (ꜰʀᴇᴇ ꜰɪʀᴇ ᴛᴄᴘ, ʙᴜꜰꜰᴇʀ ʙᴏᴛꜱ)
📦 <b>{to_small_caps('Auto Dependency')}</b> (ʀᴇQᴜɪʀᴇᴍᴇɴᴛꜱ.ᴛxᴛ / ɪᴍᴘᴏʀᴛ ᴅᴇᴛᴇᴄᴛ)
📜 <b>{to_small_caps('Real-Time Console Stream')}</b> & ᴏɴᴇ-ᴄʟɪᴄᴋ ʀᴇꜱᴛᴀʀᴛ
🌐 <b>{to_small_caps('Render Ready')}</b> (ʜᴛᴛᴘ ᴡᴇʙ ꜱᴇʀᴠɪᴄᴇ ɪɴᴛᴇɢʀᴀᴛᴇᴅ)

📢 <b>{to_small_caps('Updates Channel')}:</b> {UPDATE_CHANNEL}
━━━━━━━━━━━━━━━━━━━━━━━
⚡ <i>{to_small_caps('Deploy your bots and scripts effortlessly.')}</i>
🏷️ <b>{POWERED_BY_TEXT}</b>
    """
    kb = admin_menu_kb() if user_id in admin_ids else main_menu_kb()
    bot.send_message(message.chat.id, welcome_text, reply_markup=kb)

@bot.message_handler(commands=['status', 'stats', 'statistics'])
def stats_command(message):
    user_id = message.from_user.id
    if is_user_banned(user_id): return
    
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT user_id) FROM users")
    user_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM files")
    file_count = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM files WHERE status='Running'")
    running_count = cur.fetchone()[0] or 0
    
    cpu, memory, _ = get_system_load()
    
    stats_text = f"""
📊 <b>{to_small_caps('System Statistics')}</b>
━━━━━━━━━━━━━━━━━━━━━━━
🆔 <b>{to_small_caps('Your ID')}:</b> <code>{user_id}</code>
👥 <b>{to_small_caps('Total Users')}:</b> <code>{user_count}</code>
📁 <b>{to_small_caps('Hosted Projects')}:</b> <code>{file_count}</code>
🚀 <b>{to_small_caps('Active Engines')}:</b> <code>{running_count}</code>
⚡ <b>{to_small_caps('CPU Load')}:</b> <code>{cpu:.1f}%</code>
💾 <b>{to_small_caps('RAM Usage')}:</b> <code>{memory:.1f}%</code>
⏱ <b>{to_small_caps('Bot Uptime')}:</b> <code>{get_uptime()}</code>
━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>{POWERED_BY_TEXT}</b>
    """
    bot.send_message(message.chat.id, stats_text)

@bot.message_handler(commands=['uptime'])
def uptime_command(message):
    bot.reply_to(message, f"⏱ <b>{to_small_caps('Server Uptime')}:</b> <code>{get_uptime()}</code>\n🆔 <b>{to_small_caps('Chat ID')}:</b> <code>{message.chat.id}</code>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

@bot.message_handler(commands=['ping'])
def ping_command(message):
    start = time.time()
    msg = bot.reply_to(message, f"⚡ {to_small_caps('Measuring latency...')}")
    latency = round((time.time() - start) * 1000, 2)
    bot.edit_message_text(
        f"🚀 <b>{to_small_caps('Server Latency')}:</b> <code>{latency}ms</code>\n"
        f"⏱ <b>{to_small_caps('Uptime')}:</b> <code>{get_uptime()}</code>\n"
        f"🆔 <b>{to_small_caps('User ID')}:</b> <code>{message.from_user.id}</code>\n\n"
        f"🏷️ <b>{POWERED_BY_TEXT}</b>",
        message.chat.id, msg.message_id
    )

@bot.message_handler(commands=['mpx'])
def mpx_command(message):
    user_id = message.from_user.id
    if is_user_banned(user_id): return
    query = message.text.replace('/mpx', '', 1).strip()
    if not query:
        bot.reply_to(message, f"💡 {to_small_caps('Usage')}: <code>/mpx {to_small_caps('your query')}</code>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    bot.send_chat_action(message.chat.id, 'typing')
    try:
        response = requests.get(f"https://api.hercai.pw/v3/hercai?question={query}", timeout=25)
        if response.status_code == 200:
            ans = response.json().get('reply', 'No reply.')
            bot.reply_to(message, f"🤖 <b>{to_small_caps('MPX AI Response')}:</b>\n\n{ans}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        else:
            bot.reply_to(message, f"⚠️ {to_small_caps('AI core is momentarily busy.')}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
    except Exception as e:
        bot.reply_to(message, f"❌ <b>{to_small_caps('Error')}:</b> {e}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

# ----------------------------------------------------
# TEXT MENU HANDLERS
# ----------------------------------------------------
@bot.message_handler(func=lambda m: m.text and to_small_caps("Updates Channel") in m.text)
def updates_handler(message):
    bot.send_message(message.chat.id, f"📢 <b>{to_small_caps('Official Updates Channel')}:</b>\n{UPDATE_CHANNEL}\n\n🆔 <b>{to_small_caps('Chat ID')}:</b> <code>{message.chat.id}</code>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

@bot.message_handler(func=lambda m: m.text and to_small_caps("Uptime") in m.text)
def uptime_menu_handler(message):
    uptime_command(message)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Upload File") in m.text)
def upload_menu_handler(message):
    _logic_upload_file(message)

@bot.message_handler(func=lambda m: m.text and to_small_caps("My Files") in m.text)
def files_menu_handler(message):
    send_files_list(message.chat.id, message.from_user.id)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Favorites") in m.text)
def favorites_menu_handler(message):
    user_id = message.from_user.id
    fav_ids = get_favorites(user_id)
    if not fav_ids:
        bot.reply_to(message, f"⭐ <b>{to_small_caps('No favorites pinned yet!')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    text = f"⭐ <b>{to_small_caps('Pinned Favorite Projects')}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
    for file_id in fav_ids:
        rec = get_file_record(file_id)
        if rec:
            st = "🟢" if rec['status'] == "Running" else "🔴"
            text += f"{st} <code>{rec['orig_name']}</code> ({to_small_caps(rec['file_type'])})\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━━━\n🏷️ <b>{POWERED_BY_TEXT}</b>"
    bot.reply_to(message, text)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Search Files") in m.text)
def search_menu_handler(message):
    bot.reply_to(message, f"🔍 {to_small_caps('Send /search <filename> to find any file in your storage.')}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

@bot.message_handler(func=lambda m: m.text and to_small_caps("Bot Speed") in m.text)
def speed_menu_handler(message):
    _logic_bot_speed(message)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Statistics") in m.text)
def stats_menu_handler(message):
    stats_command(message)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Contact Owner") in m.text)
def contact_menu_handler(message):
    bot.send_message(message.chat.id, f"📞 <b>{to_small_caps('Direct Support & Dev Contact')}:</b>\n{YOUR_USERNAME}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

@bot.message_handler(func=lambda m: m.text and to_small_caps("MPX AI") in m.text)
def mpx_menu_handler(message):
    bot.reply_to(message, f"🤖 <b>{to_small_caps('MPX AI Prompt Engine')}</b>\n{to_small_caps('Use /mpx followed by your question.')}\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

@bot.message_handler(func=lambda m: m.text and to_small_caps("Manual Install") in m.text)
def manual_install_menu_handler(message):
    _logic_manual_install(message)

@bot.message_handler(func=lambda m: m.text and to_small_caps("Help") in m.text)
def help_menu_handler(message):
    text = f"""
🆘 <b>{to_small_caps('𝙲𝚁𝙰𝙲𝙺 CODEX USER MANUAL')}</b>
━━━━━━━━━━━━━━━━━━━━━━━
📁 <b>{to_small_caps('Uploading Bots & Scripts')}:</b>
• ꜱᴇɴᴅ ᴀɴʏ <code>.py</code>, <code>.js</code>, ᴏʀ <code>.zip</code> ꜰɪʟᴇ.
• ᴢɪᴘ ꜰɪʟᴇꜱ ᴄᴀɴ ɪɴᴄʟᴜᴅᴇ <code>requirements.txt</code>.
• ꜰʀᴇᴇ ꜰɪʀᴇ ᴛᴄᴘ & ᴀɪᴏɢʀᴀᴍ ʙᴏᴛꜱ ᴀʀᴇ ꜱᴜᴘᴘᴏʀᴛᴇᴅ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ.

🕹️ <b>{to_small_caps('Execution Commands')}:</b>
• /start - ʀᴇʟᴏᴀᴅ ᴍᴀɪɴ ᴍᴇɴᴜ
• /stats - ᴠɪᴇᴡ ꜱᴇʀᴠᴇʀ ᴍᴇᴛʀɪᴄꜱ
• /ping - ᴛᴇꜱᴛ ʟᴀᴛᴇɴᴄʏ
• /search - ꜰɪɴᴅ ʏᴏᴜʀ ᴘʀᴏᴊᴇᴄᴛꜱ

🆔 <b>{to_small_caps('Your Chat ID')}:</b> <code>{message.chat.id}</code>
━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>{POWERED_BY_TEXT}</b>
    """
    bot.reply_to(message, text)

# ----------------------------------------------------
# ADMIN EXCLUSIVE TEXT BUTTONS
# ----------------------------------------------------
@bot.message_handler(func=lambda m: m.text and to_small_caps("Admin Panel") in m.text)
def admin_panel_button(message):
    if message.from_user.id not in admin_ids: return
    bot.reply_to(message, f"👑 <b>{to_small_caps('Control Dashboard')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>", reply_markup=admin_panel_kb())

@bot.message_handler(func=lambda m: m.text and to_small_caps("Run All Files") in m.text)
def run_all_button(message):
    if message.from_user.id not in admin_ids: return
    _logic_run_all_scripts(message)

# ----------------------------------------------------
# DOCUMENT UPLOAD & EXECUTION PIPELINE
# ----------------------------------------------------
@bot.message_handler(content_types=['document'])
def document_handler(message):
    user_id = message.from_user.id
    if is_user_banned(user_id): return
    if bot_locked and user_id not in admin_ids:
        bot.reply_to(message, f"🔒 <b>{to_small_caps('Bot is temporarily in maintenance mode.')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    
    user_files = list_user_files(user_id)
    limit = get_user_file_limit(user_id)
    if len(user_files) >= limit:
        bot.reply_to(message, f"❌ <b>{to_small_caps('Storage quota reached')} ({len(user_files)}/{limit})</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    
    original_filename = message.document.file_name or "unknown"
    file_type = get_file_type(original_filename)
    if file_type == "unknown":
        bot.reply_to(message, f"❌ <b>{to_small_caps('Unsupported file type! Only .py, .js, .zip, .tar allowed.')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        file_bytes = bot.download_file(file_info.file_path)
    except Exception as e:
        bot.reply_to(message, f"❌ <b>{to_small_caps('Download failed')}:</b> {e}")
        return
    
    user_dir = os.path.join(UPLOADS_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    safe_filename = f"{int(time.time())}_{original_filename}"
    file_path = os.path.join(user_dir, safe_filename)
    
    with open(file_path, 'wb') as f:
        f.write(file_bytes)
    
    final_path = file_path
    extracted_dir = None
    
    if file_type in ["zip", "archive"]:
        status_msg = bot.reply_to(message, f"📦 <b>{to_small_caps('Extracting project archive...')}</b>")
        extracted_dir = os.path.join(TEMP_DIR, f"extracted_{user_id}_{int(time.time())}")
        os.makedirs(extracted_dir, exist_ok=True)
        success, error = extract_archive(file_path, extracted_dir)
        if not success:
            bot.edit_message_text(f"❌ <b>{to_small_caps('Extraction failed')}:</b> {error}", message.chat.id, status_msg.message_id)
            return
        
        main_file = find_main_file(extracted_dir)
        if not main_file:
            bot.edit_message_text(f"❌ <b>{to_small_caps('No executable .py or .js entry file found in archive.')}</b>", message.chat.id, status_msg.message_id)
            return
        final_path = extracted_dir
        file_type = get_file_type(main_file)
        bot.edit_message_text(f"✅ <b>{to_small_caps('Entry file detected')}:</b> <code>{os.path.basename(main_file)}</code>", message.chat.id, status_msg.message_id)
    
    file_id = add_file_record(user_id, message.from_user.username or "", safe_filename, original_filename, final_path, file_type)
    
    with db_lock:
        cur = conn.cursor()
        cur.execute('UPDATE bot_stats SET stat_value = stat_value + 1 WHERE stat_name = ?', ('total_uploads',))
        conn.commit()
    
    bot.reply_to(message, f"🚀 <b>{to_small_caps('Project successfully uploaded & registered!')}</b>\n🆔 <b>{to_small_caps('User ID')}:</b> <code>{user_id}</code>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
    start_file_process(file_id, message.chat.id)

def _logic_upload_file(message):
    bot.reply_to(
        message, 
        f"📤 <b>{to_small_caps('Upload Your Project')}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• ꜱᴇɴᴅ ᴀɴʏ <code>.py</code>, <code>.js</code>, ᴏʀ <code>.zip</code> ᴀʀᴄʜɪᴠᴇ.\n"
        f"• ᴀᴜᴛᴏ-ɪɴꜱᴛᴀʟʟꜱ <code>requirements.txt</code> ᴀɴᴅ ɴᴇᴇᴅᴇᴅ ᴍᴏᴅᴜʟᴇꜱ.\n"
        f"• ꜱᴜᴘᴘᴏʀᴛꜱ ᴀꜱʏɴᴄ ᴛᴇʟᴇɢʀᴀᴍ ʙᴏᴛꜱ & ᴛᴄᴘ ɴᴇᴛᴡᴏʀᴋ ꜱᴄʀɪᴘᴛꜱ.\n\n"
        f"🆔 <b>{to_small_caps('Chat ID')}:</b> <code>{message.chat.id}</code>\n"
        f"🏷️ <b>{POWERED_BY_TEXT}</b>"
    )

def _logic_bot_speed(message):
    cpu, memory, processes_count = get_system_load()
    uptime_td = datetime.utcnow() - START_TIME
    days = uptime_td.days
    hours, remainder = divmod(uptime_td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{days}ᴅ {hours}ʜ {minutes}ᴍ"
    
    bot.send_message(
        message.chat.id,
        f"⚡ <b>{to_small_caps('Live Engine Health')}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• <b>{to_small_caps('CPU Load')}:</b> <code>{cpu:.1f}%</code>\n"
        f"• <b>{to_small_caps('Memory Load')}:</b> <code>{memory:.1f}%</code>\n"
        f"• <b>{to_small_caps('Active Threads')}:</b> <code>{processes_count}/{MAX_RUNNING_PROCESSES}</code>\n"
        f"• <b>{to_small_caps('Total Uptime')}:</b> <code>{uptime_str}</code>\n"
        f"• <b>{to_small_caps('User ID')}:</b> <code>{message.from_user.id}</code>\n━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>{POWERED_BY_TEXT}</b>"
    )

def _logic_run_all_scripts(message):
    bot.reply_to(message, f"🔄 <b>{to_small_caps('Booting all registered projects...')}</b>")
    cur = conn.cursor()
    cur.execute("SELECT id FROM files WHERE status='Stopped'")
    files = cur.fetchall()
    started = 0
    for (fid,) in files:
        try:
            start_file_process(fid, message.chat.id)
            started += 1
            time.sleep(0.3)
        except Exception:
            pass
    bot.reply_to(message, f"✅ <b>{to_small_caps(f'Successfully booted {started} files!')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

def _logic_manual_install(message):
    msg = bot.reply_to(message, f"📦 <b>{to_small_caps('Enter pip package name to install (e.g. aiohttp, requests)')}:</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
    bot.register_next_step_handler(msg, process_manual_install)

def process_manual_install(message):
    if not message.text or message.text.startswith('/'): return
    module = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')
    res = subprocess.run([sys.executable, "-m", "pip", "install", module], capture_output=True, text=True, timeout=180)
    if res.returncode == 0:
        bot.reply_to(message, f"✅ <b>{to_small_caps(f'Installed {module} successfully!')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
    else:
        bot.reply_to(message, f"❌ <b>{to_small_caps(f'Failed to install {module}')}:</b>\n<pre>{html_lib.escape(res.stderr[:400])}</pre>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")

# ----------------------------------------------------
# PROCESS RUNTIME ENGINE
# ----------------------------------------------------
def start_file_process(file_id, chat_id):
    should_stop, reason = should_stop_due_to_load()
    if should_stop:
        bot.send_message(chat_id, f"⚠️ <b>{to_small_caps('Cannot start')}:</b> {reason}")
        return
    
    file_record = get_file_record(file_id)
    if not file_record: return
    
    file_path = file_record["path"]
    original_name = file_record["orig_name"]
    
    if os.path.isdir(file_path):
        main_file = find_main_file(file_path)
        if not main_file:
            bot.send_message(chat_id, f"❌ <b>{to_small_caps('No main file located.')}</b>")
            return
        target_file = main_file
        working_dir = os.path.dirname(main_file)
    else:
        if not os.path.exists(file_path):
            bot.send_message(chat_id, f"❌ <b>{to_small_caps('File not found')}</b>")
            return
        target_file = file_path
        working_dir = os.path.dirname(file_path)
    
    ext = os.path.splitext(target_file)[1].lower()
    
    # Auto-handle dependencies
    if ext == ".py":
        req_path = os.path.join(working_dir, "requirements.txt")
        if os.path.exists(req_path):
            install_requirements_from_file(req_path)
        imports = extract_imports(target_file)
        if imports:
            install_missing_imports(imports)
        cmd = [sys.executable, "-u", target_file]
    elif ext == ".js":
        cmd = ["node", target_file]
    else:
        bot.send_message(chat_id, f"❌ <b>{to_small_caps('Unsupported engine format.')}</b>")
        return
    
    log_filename = f"file_{file_id}_{int(time.time())}.log"
    log_path = os.path.join(LOGS_DIR, log_filename)
    
    try:
        log_file = open(log_path, 'w', buffering=1, encoding='utf-8', errors='ignore')
        # Pass full environment for socket/aiohttp/asyncio support
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        process = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            env=env,
            text=True
        )
        
        run_id = record_run_start(file_id, process.pid, log_path)
        update_file_status(file_id, process.pid, "Running")
        
        with proc_lock:
            processes[file_id] = {
                'process': process,
                'run_id': run_id,
                'log_path': log_path,
                'log_file': log_file,
                'started_at': datetime.utcnow().isoformat()
            }
        
        bot.send_message(
            chat_id, 
            f"🚀 <b>{to_small_caps('Launched')}:</b> <code>{html_lib.escape(original_name)}</code>\n"
            f"⚡ <b>{to_small_caps('PID')}:</b> <code>{process.pid}</code>\n"
            f"🆔 <b>{to_small_caps('Chat ID')}:</b> <code>{chat_id}</code>\n\n"
            f"🏷️ <b>{POWERED_BY_TEXT}</b>"
        )
        
        def monitor():
            try:
                exit_code = process.wait()
            except Exception:
                exit_code = -1
            finally:
                try: log_file.close()
                except Exception: pass
                update_file_status(file_id, None, "Stopped")
                record_run_finish(run_id, exit_code)
                with proc_lock:
                    processes.pop(file_id, None)
                if exit_code != 0:
                    try:
                        bot.send_message(chat_id, f"⚠️ <b>{html_lib.escape(original_name)}</b> {to_small_caps('stopped with exit code')}: <code>{exit_code}</code>")
                    except Exception:
                        pass
        
        threading.Thread(target=monitor, daemon=True).start()
    except Exception as e:
        bot.send_message(chat_id, f"❌ <b>{to_small_caps('Execution Error')}:</b> {e}")

def stop_file_process(file_id):
    with proc_lock:
        if file_id in processes:
            pinfo = processes[file_id]
            proc = pinfo['process']
            try:
                if proc.poll() is None:
                    proc.terminate()
                    try: proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception:
                pass
            try: pinfo['log_file'].close()
            except Exception: pass
            processes.pop(file_id, None)
    update_file_status(file_id, None, "Stopped")

def get_file_logs(file_id, lines=60):
    with proc_lock:
        if file_id in processes:
            lpath = processes[file_id]['log_path']
            if os.path.exists(lpath):
                with open(lpath, 'r', encoding='utf-8', errors='ignore') as f:
                    c = f.readlines()
                return ''.join(c[-lines:]) if c else to_small_caps("No console logs captured yet.")
    
    cur = conn.cursor()
    cur.execute("SELECT log_path FROM runs WHERE file_id=? ORDER BY started_at DESC LIMIT 1", (file_id,))
    row = cur.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        with open(row[0], 'r', encoding='utf-8', errors='ignore') as f:
            c = f.readlines()
        return ''.join(c[-lines:]) if c else to_small_caps("Empty log file.")
    return to_small_caps("No logs available for this project.")

def send_files_list(chat_id, user_id):
    files = list_user_files(user_id)
    if not files:
        bot.send_message(chat_id, f"📁 <b>{to_small_caps('Your Cloud Storage is empty!')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        return
    
    text = f"📁 <b>{to_small_caps('Your Hosted Projects')}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n🆔 <b>{to_small_caps('User ID')}:</b> <code>{user_id}</code>\n"
    kb = InlineKeyboardMarkup()
    for f in files:
        fid, fname, oname, uat, ftype, status, pid = f
        emoji = "🟢" if status == "Running" else "🔴"
        btn_txt = f"{emoji} {oname} [{to_small_caps(ftype)}]"
        kb.add(InlineKeyboardButton(btn_txt, callback_data=f"manage:{fid}"))
    text += f"━━━━━━━━━━━━━━━━━━━━━━━\n🏷️ <b>{POWERED_BY_TEXT}</b>"
    bot.send_message(chat_id, text, reply_markup=kb)

def show_file_management(chat_id, file_id, user_id, message_id=None):
    rec = get_file_record(file_id)
    if not rec:
        bot.send_message(chat_id, f"❌ {to_small_caps('File not found')}")
        return
    if rec["user_id"] != user_id and user_id not in admin_ids:
        bot.send_message(chat_id, f"❌ {to_small_caps('Unauthorized access')}")
        return
    
    is_running = file_id in processes
    is_fav = file_id in get_favorites(user_id)
    st_text = f"🟢 {to_small_caps('Running')}" if is_running else f"🔴 {to_small_caps('Stopped')}"
    pid_text = f"\n⚡ <b>{to_small_caps('PID')}:</b> <code>{rec['pid']}</code>" if rec['pid'] else ""
    
    text = f"""
⚙️ <b>{to_small_caps('Project Control Panel')}</b>
━━━━━━━━━━━━━━━━━━━━━━━
📁 <b>{to_small_caps('Name')}:</b> <code>{html_lib.escape(rec['orig_name'])}</code>
📊 <b>{to_small_caps('Engine')}:</b> <code>{to_small_caps(rec['file_type'])}</code>
📈 <b>{to_small_caps('Status')}:</b> {st_text}{pid_text}
⭐ <b>{to_small_caps('Favorite')}:</b> {'ʏᴇꜱ' if is_fav else 'ɴᴏ'}
⏰ <b>{to_small_caps('Uploaded')}:</b> <code>{rec['uploaded_at'][:16]}</code>
🆔 <b>{to_small_caps('Chat ID')}:</b> <code>{chat_id}</code>
━━━━━━━━━━━━━━━━━━━━━━━
🏷️ <b>{POWERED_BY_TEXT}</b>
    """
    kb = file_actions_kb(file_id, is_running)
    if message_id:
        try: bot.edit_message_text(text, chat_id, message_id, reply_markup=kb)
        except Exception: bot.send_message(chat_id, text, reply_markup=kb)
    else:
        bot.send_message(chat_id, text, reply_markup=kb)

# ----------------------------------------------------
# CALLBACK HANDLER
# ----------------------------------------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    data = call.data
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    if data == "back_to_files":
        try: bot.delete_message(chat_id, call.message.message_id)
        except Exception: pass
        send_files_list(chat_id, user_id)
        return
    
    if data == "back_to_main":
        try: bot.delete_message(chat_id, call.message.message_id)
        except Exception: pass
        kb = admin_menu_kb() if user_id in admin_ids else main_menu_kb()
        bot.send_message(chat_id, f"🏠 <b>{to_small_caps('Main Menu')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>", reply_markup=kb)
        return
    
    if data.startswith("manage:"):
        fid = int(data.split(":")[1])
        show_file_management(chat_id, fid, user_id, call.message.message_id)
    elif data.startswith("start:"):
        fid = int(data.split(":")[1])
        bot.answer_callback_query(call.id, to_small_caps("Starting engine..."))
        start_file_process(fid, chat_id)
        time.sleep(1)
        show_file_management(chat_id, fid, user_id, call.message.message_id)
    elif data.startswith("stop:"):
        fid = int(data.split(":")[1])
        bot.answer_callback_query(call.id, to_small_caps("Stopping engine..."))
        stop_file_process(fid)
        time.sleep(1)
        show_file_management(chat_id, fid, user_id, call.message.message_id)
    elif data.startswith("restart:"):
        fid = int(data.split(":")[1])
        bot.answer_callback_query(call.id, to_small_caps("Rebooting engine..."))
        stop_file_process(fid)
        time.sleep(1.5)
        start_file_process(fid, chat_id)
        time.sleep(1)
        show_file_management(chat_id, fid, user_id, call.message.message_id)
    elif data.startswith("fav:"):
        fid = int(data.split(":")[1])
        is_fav = toggle_favorite(user_id, fid)
        bot.answer_callback_query(call.id, to_small_caps("Pinned to favorites!" if is_fav else "Removed from favorites!"))
        show_file_management(chat_id, fid, user_id, call.message.message_id)
    elif data.startswith("delete:"):
        fid = int(data.split(":")[1])
        rec = get_file_record(fid)
        if rec:
            stop_file_process(fid)
            try:
                if os.path.isdir(rec["path"]): shutil.rmtree(rec["path"], ignore_errors=True)
                elif os.path.exists(rec["path"]): os.remove(rec["path"])
            except Exception: pass
            remove_file_record(fid)
        bot.answer_callback_query(call.id, to_small_caps("File deleted!"))
        send_files_list(chat_id, user_id)
    elif data.startswith("logs:"):
        fid = int(data.split(":")[1])
        bot.answer_callback_query(call.id, to_small_caps("Streaming logs..."))
        logs = get_file_logs(fid)
        rec = get_file_record(fid)
        fname = rec["orig_name"] if rec else "Unknown"
        bot.send_message(
            chat_id, 
            f"📄 <b>{to_small_caps('Live Logs')}:</b> <code>{html_lib.escape(fname)}</code>\n\n<pre>{html_lib.escape(logs[-3800:])}</pre>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>"
        )
    elif data == "admin_system_status":
        if user_id not in admin_ids: return
        cpu, mem, proc = get_system_load()
        text = f"⚙️ <b>{to_small_caps('Server Diagnostics')}</b>\n━━━━━━━━━━━━━━━━━━━━━━━\n⚡ <b>{to_small_caps('CPU')}:</b> <code>{cpu:.1f}%</code>\n💾 <b>{to_small_caps('Memory')}:</b> <code>{mem:.1f}%</code>\n🚀 <b>{to_small_caps('Processes')}:</b> <code>{proc}</code>\n⏱ <b>{to_small_caps('Uptime')}:</b> <code>{get_uptime()}</code>\n━━━━━━━━━━━━━━━━━━━━━━━\n🏷️ <b>{POWERED_BY_TEXT}</b>"
        bot.send_message(chat_id, text)
    elif data == "admin_backup_db":
        if user_id not in admin_ids: return
        bpath = os.path.join(DATA_DIR, f"backup_{int(time.time())}.db")
        shutil.copy(DB_PATH, bpath)
        with open(bpath, 'rb') as f:
            bot.send_document(chat_id, f, caption=f"💾 <b>{to_small_caps('Database Backup Snapshot')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        try: os.remove(bpath)
        except Exception: pass
    elif data == "admin_clean_files":
        if user_id not in admin_ids: return
        deleted = 0
        for f in os.listdir(LOGS_DIR):
            p = os.path.join(LOGS_DIR, f)
            if os.path.getmtime(p) < (time.time() - 7*24*3600):
                os.remove(p)
                deleted += 1
        bot.send_message(chat_id, f"🗑️ <b>{to_small_caps(f'Purged {deleted} expired log files!')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
    elif data == "admin_restart_bot":
        if user_id != OWNER_ID: return
        bot.send_message(chat_id, f"🔄 <b>{to_small_caps('Restarting hosting daemon...')}</b>\n\n🏷️ <b>{POWERED_BY_TEXT}</b>")
        for fid in list(processes.keys()):
            stop_file_process(fid)
        time.sleep(2)
        os.execl(sys.executable, sys.executable, *sys.argv)

# ----------------------------------------------------
# MAIN ENTRYPOINT
# ----------------------------------------------------
if __name__ == "__main__":
    logger.info("🔥 LAUNCHING WEB SERVICE DAEMON...")
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    logger.info("⚡ STARTING 𝙲𝚁𝙰𝙲𝙺 CODEX POLLING LOOP...")
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=50)
        except Exception as e:
            logger.error(f"Polling loop encountered: {e}")
            time.sleep(4)