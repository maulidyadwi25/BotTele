"""
Bot Telegram Production - Webhook Version
Gunakan file ini untuk production deployment dengan webhook.
Untuk development, gunakan bot.py dengan run_polling().
"""
import os
import json
import base64
import random
from dotenv import load_dotenv

# Load .env file - prioritize .env.production if exists
if os.path.exists('.env.production'):
    load_dotenv('.env.production')
else:
    load_dotenv()

import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import gsheets_service as gs
from ai_service import get_ai_provider

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PARSE_MODE = os.getenv("TELEGRAM_PARSE_MODE", "HTML")
FOLDER_ID = os.getenv('FOLDER_ID', '')

# Webhook configuration
WEBHOOK_MODE = os.getenv('WEBHOOK_MODE', 'true').lower() == 'true'
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '')  # e.g., https://yourdomain.com
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook/' + TELEGRAM_BOT_TOKEN.split(':')[0])
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')  # Secret token for webhook verification
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
SERVER_PORT = int(os.getenv('SERVER_PORT', '8080'))

ai_provider = get_ai_provider()
print(f"AI Provider aktif: {os.getenv('AI_PROVIDER')}")
print(f"Webhook mode: {WEBHOOK_MODE}")

# Cache data sheet
data_cache = {"content": None, "timestamp": 0}
CACHE_DURATION = 60

# Callback data cache untuk menghindari data terlalu panjang
callback_cache = {}

def get_sheet_data():
    """Wrapper untuk mengambil data dari semua file dan sheet."""
    return gs.get_all_data_from_folder()

def encode_callback_data(data):
    """Encode callback data untuk menghindari batasan 64 bytes."""
    if len(data) <= 64:
        return data
    import hashlib
    key = hashlib.md5(data.encode()).hexdigest()[:16]
    callback_cache[key] = data
    return f"cache_{key}"

def decode_callback_data(data):
    """Decode callback data dari cache jika diperlukan."""
    if data.startswith("cache_"):
        key = data.split("_", 1)[1]
        return callback_cache.get(key, data)
    return data

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan daftar file spreadsheet dan folder sebagai inline keyboard buttons."""
    keyboard = []
    
    spreadsheet_files = gs.get_spreadsheet_files()
    
    if not spreadsheet_files:
        await update.message.reply_text("Tidak ada file spreadsheet yang ditemukan di folder.")
        return
    
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']
        
        if file.get('is_folder', False):
            display_name = f"[Folder] {file_name}"
            callback_data = encode_callback_data(f"folder_{file_id}")
        else:
            parent_folder_name = file.get('parent_folder_name')
            if parent_folder_name:
                display_name = f"[Sheet] {file_name} (dari folder: {parent_folder_name})"
            else:
                display_name = f"[Sheet] {file_name}"
            callback_data = encode_callback_data(f"file_{file_id}")
        
        keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "Daftar File Spreadsheet dan Folder\n\n"
        "Silakan pilih file atau folder yang ingin Anda lihat:",
        reply_markup=reply_markup,
        parse_mode=TELEGRAM_PARSE_MODE
    )

async def sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan semua sheet dari semua file spreadsheet."""
    spreadsheet_files = gs.get_spreadsheet_files()
    
    if not spreadsheet_files:
        await update.message.reply_text("Tidak ada file spreadsheet yang ditemukan di folder.")
        return
    
    output = "Daftar Semua Sheet\n\n"
    
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']
        
        output += f"*File:* {file_name}\n"
        
        sheets = gs.get_sheets_from_file(file_id)
        
        if not sheets:
            output += "   Gagal mengambil sheet\n"
        else:
            for sheet_name in sheets:
                output += f"   [Sheet] {sheet_name}\n"
        
        output += "\n"
    
    await update.message.reply_text(output, parse_mode=TELEGRAM_PARSE_MODE)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani callback query dari inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    data = decode_callback_data(query.data)
    
    if data.startswith("folder_"):
        folder_id = data.split("_", 1)[1]
        context.user_data['current_folder_id'] = folder_id
        
        files = gs.get_files_in_folder(folder_id)
        
        if not files:
            await query.edit_message_text("Folder ini kosong atau tidak dapat diakses.")
            return
        
        keyboard = []
        for file in files:
            file_id = file['id']
            file_name = file['name']
            
            if file.get('is_folder', False):
                display_name = f"[Folder] {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                display_name = f"[Sheet] {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        if files:
            parent_folder_id = files[0].get('parent_folder_id')
            if parent_folder_id and parent_folder_id != FOLDER_ID:
                keyboard.append([InlineKeyboardButton("<< Kembali ke Folder Sebelumnya", callback_data=encode_callback_data(f"folder_{parent_folder_id}"))])
            else:
                keyboard.append([InlineKeyboardButton("<< Kembali ke Daftar Utama", callback_data="back_to_root")])
        else:
            keyboard.append([InlineKeyboardButton("<< Kembali ke Daftar Utama", callback_data="back_to_root")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        folder_num = len(files)
        
        folder_desc = f"Isi Folder ({folder_num} item)\n"
        folder_desc += f"ID: {folder_id[:8]}...\n"
        folder_desc += f"Timestamp: {timestamp}-{random_num}\n\n"
        folder_desc += f"Silakan pilih file atau folder yang ingin Anda lihat:"
        
        await query.edit_message_text(
            folder_desc,
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data.startswith("file_"):
        file_id = data.split("_", 1)[1]
        file_name = gs.get_file_name(file_id)
        
        context.user_data['selected_file_id'] = file_id
        context.user_data['selected_file_name'] = file_name
        
        sheets = gs.get_sheets_from_file(file_id)
        
        if not sheets:
            await query.edit_message_text("Gagal mengambil daftar sheet dari file tersebut.")
            return
        
        keyboard = []
        for sheet_name in sheets:
            callback_data = encode_callback_data(f"sheet|{file_id}|{sheet_name}")
            keyboard.append([InlineKeyboardButton(sheet_name, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("<< Kembali ke Daftar File", callback_data=encode_callback_data("back_to_files"))])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"Daftar Sheet\n\n"
            f"File: {file_name}\n"
            f"Silakan pilih sheet yang ingin Anda lihat:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data.startswith("sheet|"):
        data_decoded = decode_callback_data(data)
        parts = data_decoded.replace("sheet|", "|").split("|")
        file_id = parts[1] if len(parts) > 1 else ""
        sheet_name = parts[2] if len(parts) > 2 else ""
        
        print(f"DEBUG callback data: {data}")
        print(f"DEBUG decoded: {data_decoded}")
        print(f"DEBUG parts: {parts}")
        print(f"DEBUG file_id: {file_id}, sheet_name: {sheet_name}")
        
        context.user_data['selected_file_id'] = file_id
        context.user_data['selected_sheet_name'] = sheet_name
        
        keyboard = [
            [InlineKeyboardButton("[Data] Ambil Data Lengkap", callback_data=encode_callback_data(f"action|data|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("[Stats] Hitung Rata-rata", callback_data=encode_callback_data(f"action|avg|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("[Total] Hitung Total", callback_data=encode_callback_data(f"action|total|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("[Statistik] Statistik", callback_data=encode_callback_data(f"action|stats|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("<< Kembali ke Daftar Sheet", callback_data=encode_callback_data(f"file|{file_id}"))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"Sheet: {sheet_name}\n\n"
            f"Pilih aksi yang ingin Anda lakukan:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )

    elif data.startswith("action|"):
        parts = data.replace("action|", "action|").split("|")
        action_type = parts[1]
        file_id = parts[2]
        sheet_name = parts[3]
        
        try:
            client = gs.get_sheets_client()
            spreadsheet = client.open_by_key(file_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            data_values = worksheet.get_all_values()
            
            if not data_values:
                await query.edit_message_text(f"Sheet '{sheet_name}' kosong.")
                return
            
            output = ""
            
            if action_type == "data":
                output = f"Data dari Sheet: {sheet_name}\n\n"
                
                if len(data_values) > 0:
                    header = " | ".join([str(cell) for cell in data_values[0]])
                    output += f"<code>{header}</code>\n"
                    output += "-" * len(header) + "\n"
                
                rows_to_show = min(10, len(data_values) - 1)
                for i in range(1, rows_to_show + 1):
                    row_data = " | ".join([str(cell) for cell in data_values[i]])
                    output += f"<code>{row_data}</code>\n"
                
                if len(data_values) - 1 > rows_to_show:
                    output += f"\n... dan {len(data_values) - 1 - rows_to_show} baris lainnya.\n"
            
            elif action_type == "avg":
                output = f"Rata-rata dari Sheet: {sheet_name}\n\n"
                
                numeric_columns = []
                if len(data_values) > 1:
                    for col_idx in range(len(data_values[0])):
                        is_numeric = True
                        numeric_values = []
                        for row_idx in range(1, len(data_values)):
                            try:
                                value = float(data_values[row_idx][col_idx])
                                numeric_values.append(value)
                            except (ValueError, IndexError):
                                is_numeric = False
                                break
                        
                        if is_numeric and numeric_values:
                            avg = sum(numeric_values) / len(numeric_values)
                            column_name = data_values[0][col_idx] if col_idx < len(data_values[0]) else f"Kolom {col_idx + 1}"
                            output += f"<code>{column_name}: {avg:.2f}</code>\n"
                            numeric_columns.append(column_name)
                
                if not numeric_columns:
                    output += "Tidak ada kolom numerik yang ditemukan.\n"
            
            elif action_type == "total":
                output = f"Total dari Sheet: {sheet_name}\n\n"
                
                numeric_columns = []
                if len(data_values) > 1:
                    for col_idx in range(len(data_values[0])):
                        is_numeric = True
                        numeric_values = []
                        for row_idx in range(1, len(data_values)):
                            try:
                                value = float(data_values[row_idx][col_idx])
                                numeric_values.append(value)
                            except (ValueError, IndexError):
                                is_numeric = False
                                break
                        
                        if is_numeric and numeric_values:
                            total = sum(numeric_values)
                            column_name = data_values[0][col_idx] if col_idx < len(data_values[0]) else f"Kolom {col_idx + 1}"
                            output += f"<code>{column_name}: {total:.2f}</code>\n"
                            numeric_columns.append(column_name)
                
                if not numeric_columns:
                    output += "Tidak ada kolom numerik yang ditemukan.\n"
            
            elif action_type == "stats":
                output = f"Statistik dari Sheet: {sheet_name}\n\n"
                
                numeric_columns = []
                if len(data_values) > 1:
                    for col_idx in range(len(data_values[0])):
                        is_numeric = True
                        numeric_values = []
                        for row_idx in range(1, len(data_values)):
                            try:
                                value = float(data_values[row_idx][col_idx])
                                numeric_values.append(value)
                            except (ValueError, IndexError):
                                is_numeric = False
                                break
                        
                        if is_numeric and numeric_values:
                            column_name = data_values[0][col_idx] if col_idx < len(data_values[0]) else f"Kolom {col_idx + 1}"
                            avg = sum(numeric_values) / len(numeric_values)
                            total = sum(numeric_values)
                            min_val = min(numeric_values)
                            max_val = max(numeric_values)
                            
                            output += f"<code>{column_name}:</code>\n"
                            output += f"<code>  Rata-rata: {avg:.2f}</code>\n"
                            output += f"<code>  Total: {total:.2f}</code>\n"
                            output += f"<code>  Min: {min_val:.2f}</code>\n"
                            output += f"<code>  Max: {max_val:.2f}</code>\n\n"
                            
                            numeric_columns.append(column_name)
                
                if not numeric_columns:
                    output += "Tidak ada kolom numerik yang ditemukan.\n"
            
            keyboard = [[InlineKeyboardButton("<< Kembali ke Pilihan Aksi", callback_data=encode_callback_data(f"sheet|{file_id}|{sheet_name}"))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                output,
                reply_markup=reply_markup,
                parse_mode=TELEGRAM_PARSE_MODE
            )
            
        except Exception as e:
            print(f"Error getting sheet data: {e}")
            await query.edit_message_text(f"Gagal mengambil data dari sheet: {str(e)}")
    
    elif data == "back_to_files" or data == "back_to_root":
        keyboard = []
        
        spreadsheet_files = gs.get_spreadsheet_files()
        
        if not spreadsheet_files:
            await query.edit_message_text("Tidak ada file spreadsheet yang ditemukan di folder.")
            return
        
        for file in spreadsheet_files:
            file_id = file['id']
            file_name = file['name']
            
            if file.get('is_folder', False):
                display_name = f"[Folder] {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                parent_folder_name = file.get('parent_folder_name')
                if parent_folder_name:
                    display_name = f"[Sheet] {file_name} (dari folder: {parent_folder_name})"
                else:
                    display_name = f"[Sheet] {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "Daftar File Spreadsheet dan Folder\n\n"
            "Silakan pilih file atau folder yang ingin Anda lihat:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_question = update.message.text.strip()
    if not user_question:
        return
    
    await update.message.chat.send_action(action="typing")
    
    sheet_data = get_sheet_data()
    if sheet_data is None:
        await update.message.reply_text("Gagal mengambil data dari Google Sheets.")
        return
    
    selected_file_id = context.user_data.get('selected_file_id')
    selected_sheet_name = context.user_data.get('selected_sheet_name')
    selected_file_name = context.user_data.get('selected_file_name', 'Unknown')
    
    print(f"DEBUG - selected_file_id: {selected_file_id}")
    print(f"DEBUG - selected_sheet_name: {selected_sheet_name}")
    
    if selected_file_id and selected_sheet_name:
        raw_data = gs.get_sheet_data(selected_file_id, selected_sheet_name)
        file_context = f"File '{selected_file_name}', Sheet '{selected_sheet_name}'"
        
        if raw_data:
            lines = []
            for row in raw_data[:20]:
                lines.append(" | ".join(str(c) for c in row))
            sheet_str = "\n".join(lines)
        else:
            sheet_str = "Data tidak ditemukan"
    else:
        raw_data = get_sheet_data()
        file_context = "Seluruh folder Google Drive"
        sheet_str = raw_data if raw_data else "Data tidak ditemukan"
    
    system_prompt = f"""
    Anda adalah asisten yang membantu menjawab pertanyaan berdasarkan data berikut.
    KONTEKS: {file_context}
    DATA:
    {sheet_str}

    **PERATURAN PENTING:**
    1. Jawablah HANYA berdasarkan data di atas
    2. Jangan mengubah atau mengarang data
    3. Jangan sebutkan ID file dalam jawaban
    4. Gunakan format HTML: <b>tebal</b>, <i>miring</i>, <code>data</code>
    """

    try:
        answer = ai_provider.generate_response(system_prompt, user_question)
        await update.message.reply_text(answer, parse_mode=TELEGRAM_PARSE_MODE)
    except Exception as e:
        print(f"Error AI: {e}")
        await update.message.reply_text("Maaf, terjadi kesalahan.")

async def set_webhook():
    """Set webhook URL untuk bot Telegram."""
    if not WEBHOOK_HOST:
        print("ERROR: WEBHOOK_HOST tidak diset. Set di .env.production")
        return False
    
    full_webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    print(f"Mengatur webhook ke: {full_webhook_url}")
    
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    await app.initialize()
    
    if WEBHOOK_SECRET:
        await app.bot.set_webhook(
            url=full_webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
    else:
        await app.bot.set_webhook(
            url=full_webhook_url,
            drop_pending_updates=True
        )
    
    print("Webhook berhasil diset!")
    return True

async def run_webhook():
    """Jalankan bot dengan webhook."""
    from aiohttp import web
    
    # Build application first
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("sheets", sheets_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    await app.initialize()
    
    # Set webhook
    full_webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    
    if WEBHOOK_SECRET:
        await app.bot.set_webhook(
            url=full_webhook_url,
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
    else:
        await app.bot.set_webhook(
            url=full_webhook_url,
            drop_pending_updates=True
        )
    
    print(f"Webhook aktif di: {full_webhook_url}")
    
    # Create aiohttp application
    aiohttp_app = app.webhook_app()
    
    # Add custom webhook path handler
    async def webhook_handler(request):
        """Handle incoming webhook requests."""
        if WEBHOOK_SECRET:
            secret = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
            if secret != WEBHOOK_SECRET:
                return web.Response(status=403, text='Forbidden')
        
        return await aiohttp_app.handle(request)
    
    # Route for the webhook endpoint
    aiohttp_app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    # Health check endpoint
    async def health_check(request):
        return web.Response(text='OK')
    
    aiohttp_app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(aiohttp_app)
    await runner.setup()
    site = web.TCPSite(runner, SERVER_HOST, SERVER_PORT)
    await site.start()
    
    print(f"Server berjalan di {SERVER_HOST}:{SERVER_PORT}")
    
    # Keep the server running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await runner.cleanup()

def main():
    print("Memulai bot Telegram Production (Webhook Mode)...")
    
    if WEBHOOK_MODE:
        print("=" * 50)
        print("PRODUCTION MODE - Using Webhook")
        print("=" * 50)
        asyncio.run(run_webhook())
    else:
        print("=" * 50)
        print("DEVELOPMENT MODE - Using Polling")
        print("Gunakan bot.py untuk development")
        print("=" * 50)

if __name__ == '__main__':
    main()
