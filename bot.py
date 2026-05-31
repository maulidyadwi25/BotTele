import os
import json
import base64
import random
from dotenv import load_dotenv
load_dotenv()

import asyncio
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import gsheets_service as gs
from ai_service import get_ai_provider

# Access Manager integration for permission checking
import sys
sys.path.insert(0, 'access_manager')
from access_manager.models.bot_db import TelegramUser, get_session, init_db
from access_manager.services.bot_permission_service import BotPermissionService

# Initialize database tables and permission service
init_db()
permission_service = BotPermissionService()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PARSE_MODE = os.getenv("TELEGRAM_PARSE_MODE", "HTML")  # default HTML
FOLDER_ID = os.getenv('FOLDER_ID', '')
ai_provider = get_ai_provider()
print(f"AI Provider aktif: {os.getenv('AI_PROVIDER')}")

# Cache data sheet
data_cache = {"content": None, "timestamp": 0}
CACHE_DURATION = 60

# Callback data cache untuk menghindari data terlalu panjang
callback_cache = {}

def get_sheet_data():
    """Wrapper untuk mengambil data dari semua file dan sheet."""
    # Cache bisa Anda tambahkan lagi di sini jika diperlukan
    return gs.get_all_data_from_folder()

def encode_callback_data(data):
    """Encode callback data untuk menghindari batasan 64 bytes."""
    if len(data) <= 64:
        return data
    # Gunakan cache untuk data panjang
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
    
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    display_name = update.effective_user.full_name
    
    print(f"[DEBUG] start_command - User: {username} ({telegram_id})")
    
    # Check if user is registered in access manager
    session = get_session()
    try:
        # Try to find by telegram_id first, then fallback to username
        existing_user = session.query(TelegramUser).filter_by(telegram_id=telegram_id).first()
        if not existing_user and username:
            existing_user = session.query(TelegramUser).filter_by(username=username).first()
        
        if not existing_user:
            # User NOT registered - show message and return
            print(f"[DEBUG] User {username} ({telegram_id}) is NOT registered in access manager")
            await update.message.reply_text(
                "Maaf, Anda belum terdaftar dalam sistem. Silakan hubungi administrator untuk mendapatkan akses."
            )
            return
        
        print(f"[DEBUG] User {username} found in DB - status: {existing_user.status}")
        
        # Check if user has global access (pass username for fallback lookup)
        has_global = permission_service.has_global_access(telegram_id, username)
        print(f"[DEBUG] User {username} has_global_access: {has_global}")
        
    finally:
        session.close()
    
    keyboard = []
    
    # Ambil daftar file spreadsheet dan folder
    spreadsheet_files = gs.get_spreadsheet_files()
    
    if not spreadsheet_files:
        await update.message.reply_text("Tidak ada file spreadsheet yang ditemukan di folder.")
        return
    
    print(f"[DEBUG] Total files/folders from Drive: {len(spreadsheet_files)}")
    
    # Buat button untuk setiap file dan folder - HANYA yang user punya akses
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']
        
        # Check permission for this specific file/folder (pass username for fallback)
        has_permission = permission_service.has_file_permission(telegram_id, file_id, username)
        print(f"[DEBUG] User {username} has_permission for '{file_name}': {has_permission}")
        
        # Skip files user doesn't have permission to
        if not has_permission:
            continue
        
        # Tambahkan icon folder jika itu adalah folder
        if file.get('is_folder', False):
            display_name = f"[Folder] {file_name}"
            callback_data = encode_callback_data(f"folder_{file_id}")
        else:
            # Tambahkan icon sheet jika itu adalah file spreadsheet
            parent_folder_name = file.get('parent_folder_name')
            if parent_folder_name:
                display_name = f"[File] {file_name} (dari folder: {parent_folder_name})"
            else:
                display_name = f"[File] {file_name}"
            callback_data = encode_callback_data(f"file_{file_id}")
        
        keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
    
    print(f"[DEBUG] User {username} - filtered buttons count: {len(keyboard)}")
    
    if not keyboard:
        await update.message.reply_text(
            "Anda tidak memiliki akses ke file manapun. Silakan hubungi administrator."
        )
        return
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📂 **Daftar File Spreadsheet dan Folder**\n\n"
        "Silakan pilih file atau folder yang ingin Anda lihat:",
        reply_markup=reply_markup,
        parse_mode=TELEGRAM_PARSE_MODE
    )

async def sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan semua sheet dari semua file spreadsheet."""
    spreadsheet_files = gs.get_spreadsheet_files()
    
    if not spreadsheet_files:
        await update.message.reply_text("❌ Tidak ada file spreadsheet yang ditemukan di folder.")
        return
    
    output = "📋 **Daftar Semua Sheet**\n\n"
    
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']
        
        output += f"📁 *File:* {file_name}\n"
        
        # Ambil daftar sheet dari file
        sheets = gs.get_sheets_from_file(file_id)
        
        if not sheets:
            output += "   ❌ Gagal mengambil sheet\n"
        else:
            for sheet_name in sheets:
                output += f"   📄 {sheet_name}\n"
        
        output += "\n"
    
    await update.message.reply_text(output, parse_mode=TELEGRAM_PARSE_MODE)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani callback query dari inline keyboard."""
    query = update.callback_query
    await query.answer()
    
    # Decode callback data
    data = decode_callback_data(query.data)
    
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    
    print(f"[DEBUG] handle_callback_query - User: {username} ({telegram_id}), data: {data}")
    
    if data.startswith("folder_"):
        # User memilih folder, tampilkan isi folder tersebut
        folder_id = data.split("_", 1)[1]
        
        print(f"[DEBUG] User {username} opening folder: {folder_id}")
        
        # Simpan folder ID saat ini di user_data
        context.user_data['current_folder_id'] = folder_id
        
        # Ambil daftar file dan folder dalam folder tersebut
        files = gs.get_files_in_folder(folder_id)
        
        print(f"[DEBUG] User {username} - raw files in folder: {len(files) if files else 0}")
        
        if not files:
            await query.edit_message_text("❌ Folder ini kosong atau tidak dapat diakses.")
            return
        
        keyboard = []
        filtered_count = 0
        for file in files:
            file_id = file['id']
            file_name = file['name']
            
            # Check permission for this file/folder (pass username for fallback)
            has_permission = permission_service.has_file_permission(telegram_id, file_id, username)
            print(f"[DEBUG] User {username} has_permission for '{file_name}': {has_permission}")
            
            # Skip files user doesn't have permission to
            if not has_permission:
                filtered_count += 1
                continue
            
            # Tambahkan icon folder jika itu adalah folder
            if file.get('is_folder', False):
                display_name = f"[Folder] {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                # Tambahkan icon sheet jika itu adalah file spreadsheet
                display_name = f"[File] {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        print(f"[DEBUG] User {username} - filtered out {filtered_count} items, remaining: {len(keyboard)}")
        
        # Tambahkan tombol kembali ke folder parent
        # Gunakan parent_folder_id dari file pertama (semua file di folder yang sama memiliki parent yang sama)
        if files:
            parent_folder_id = files[0].get('parent_folder_id')
            if parent_folder_id and parent_folder_id != FOLDER_ID:
                keyboard.append([InlineKeyboardButton("← Kembali ke Folder Sebelumnya", callback_data=encode_callback_data(f"folder_{parent_folder_id}"))])
            else:
                keyboard.append([InlineKeyboardButton("← Kembali ke Daftar Utama", callback_data="back_to_root")])
        else:
            keyboard.append([InlineKeyboardButton("← Kembali ke Daftar Utama", callback_data="back_to_root")])
        
        # Check if there are any accessible files (excluding back button)
        accessible_files = [btn for btn in keyboard if not btn.text.startswith("←")]
        
        if not accessible_files:
            # No accessible files - show message
            print(f"[DEBUG] User {username} has no access to any items in folder")
            await query.answer("Anda tidak memiliki akses ke item manapun di folder ini.", show_alert=True)
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Buat deskripsi folder
        folder_desc = f"📂 **Isi Folder** ({len(accessible_files)} item)\n\n"
        folder_desc += f"Silakan pilih file atau folder yang ingin Anda lihat:"
        
        await query.edit_message_text(
            folder_desc,
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data.startswith("file_"):
        # User memilih file, tampilkan daftar sheet
        file_id = data.split("_", 1)[1]
        
        print(f"[DEBUG] User {username} selecting file: {file_id}")
        
        # Check permission before showing file (pass username for fallback)
        if not permission_service.has_file_permission(telegram_id, file_id, username):
            print(f"[DEBUG] User {username} DENIED access to file: {file_id}")
            await query.answer("Access denied. You don't have permission.", show_alert=True)
            return
        
        # Ambil nama file
        file_name = gs.get_file_name(file_id)
        
        print(f"[DEBUG] User {username} accessing file: {file_name}")
        
        # Simpan selected file di context
        context.user_data['selected_file_id'] = file_id
        context.user_data['selected_file_name'] = file_name
        
        # Ambil daftar sheet dari file
        sheets = gs.get_sheets_from_file(file_id)
        
        if not sheets:
            await query.edit_message_text("❌ Gagal mengambil daftar sheet dari file tersebut.")
            return
        
        keyboard = []
        for sheet_name in sheets:
            # Gunakan callback data dengan separator | (bukan _) agar tidak terpengaruh oleh underscore di sheet name
            callback_data = encode_callback_data(f"sheet|{file_id}|{sheet_name}")
            keyboard.append([InlineKeyboardButton(sheet_name, callback_data=callback_data)])
        
        # Tambahkan tombol kembali ke daftar file
        keyboard.append([InlineKeyboardButton("← Kembali ke Daftar File", callback_data=encode_callback_data("back_to_files"))])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📄 **Daftar Sheet**\n\n"
            f"File: {file_name}\n"
            f"Silakan pilih sheet yang ingin Anda lihat:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data.startswith("sheet|"):
        # Pisahkan dengan separator khusus | agar tidak terpengaruh oleh underscore di sheet name
        # Decode data dulu jika perlu, lalu split
        data_decoded = decode_callback_data(data)
        parts = data_decoded.replace("sheet|", "|").split("|")
        file_id = parts[1] if len(parts) > 1 else ""
        sheet_name = parts[2] if len(parts) > 2 else ""
        
        print(f"[DEBUG] User {username} accessing sheet: {sheet_name} in file: {file_id}")
        
        # Check permission before showing actions (pass username for fallback)
        if not permission_service.has_file_permission(telegram_id, file_id, username):
            print(f"[DEBUG] User {username} DENIED access to file: {file_id}")
            await query.answer("Access denied. You don't have permission.", show_alert=True)
            return
        
        # Simpan informasi sheet untuk digunakan nanti
        context.user_data['selected_file_id'] = file_id
        context.user_data['selected_sheet_name'] = sheet_name
        
        # Tampilkan pilihan aksi
        keyboard = [
            [InlineKeyboardButton("Ambil Data Lengkap", callback_data=encode_callback_data(f"action|data|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("Hitung Rata-rata", callback_data=encode_callback_data(f"action|avg|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("Hitung Total", callback_data=encode_callback_data(f"action|total|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("Statistik", callback_data=encode_callback_data(f"action|stats|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("<< Kembali ke Daftar Sheet", callback_data=encode_callback_data(f"back_to_sheet_list|{file_id}"))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"**Sheet: {sheet_name}**\n\n"
            f"Pilih aksi yang ingin Anda lakukan atau tulis perintah untuk sheet ini:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )

    elif data.startswith("action|"):
        # User memilih aksi untuk sheet
        parts = data.replace("action|", "action|").split("|")
        action_type = parts[1]
        file_id = parts[2]
        sheet_name = parts[3]
        
        print(f"[DEBUG] User {username} action: {action_type} on sheet: {sheet_name} file: {file_id}")
        
        # Check permission before showing data
        # Check permission before showing data (pass username for fallback)
        if not permission_service.has_file_permission(telegram_id, file_id, username):
            print(f"[DEBUG] User {username} DENIED access to file: {file_id}")
            await query.answer("Access denied. You don't have permission.", show_alert=True)
            return
        
        # Ambil data dari sheet tertentu
        try:
            client = gs.get_sheets_client()
            spreadsheet = client.open_by_key(file_id)
            worksheet = spreadsheet.worksheet(sheet_name)
            
            # Ambil semua data dari sheet
            data_values = worksheet.get_all_values()
            
            if not data_values:
                await query.edit_message_text(f"❌ Sheet '{sheet_name}' kosong.")
                return
            
            output = ""
            
            if action_type == "data":
                # Tampilkan data lengkap
                output = f"📋 **Data dari Sheet: {sheet_name}**\n\n"
                
                # Tampilkan header (baris pertama)
                if len(data_values) > 0:
                    header = " | ".join([str(cell) for cell in data_values[0]])
                    output += f"<code>{header}</code>\n"
                    output += "-" * len(header) + "\n"
                
                # Tampilkan data (batasi untuk menghindari output terlalu panjang)
                rows_to_show = min(10, len(data_values) - 1)
                for i in range(1, rows_to_show + 1):
                    row_data = " | ".join([str(cell) for cell in data_values[i]])
                    output += f"<code>{row_data}</code>\n"
                
                if len(data_values) - 1 > rows_to_show:
                    output += f"\n... dan {len(data_values) - 1 - rows_to_show} baris lainnya.\n"
            
            elif action_type == "avg":
                # Hitung rata-rata dari kolom numerik
                output = f"📊 **Rata-rata dari Sheet: {sheet_name}**\n\n"
                
                # Cari kolom numerik
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
                # Hitung total dari kolom numerik
                output = f"🔢 **Total dari Sheet: {sheet_name}**\n\n"
                
                # Cari kolom numerik
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
                # Tampilkan statistik dasar
                output = f"📈 **Statistik dari Sheet: {sheet_name}**\n\n"
                
                # Cari kolom numerik
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
            
            # Tambahkan tombol kembali ke sheet list dan file list
            keyboard = [
                [InlineKeyboardButton("<< Kembali ke Daftar Sheet", callback_data=encode_callback_data(f"back_to_sheet_list|{file_id}"))],
                [InlineKeyboardButton("← Kembali ke Daftar File", callback_data=encode_callback_data("back_to_files"))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                output,
                reply_markup=reply_markup,
                parse_mode=TELEGRAM_PARSE_MODE
            )
            
        except Exception as e:
            print(f"Error getting sheet data: {e}")
            await query.edit_message_text(f"❌ Gagal mengambil data dari sheet: {str(e)}")
    
    elif data.startswith("back_to_sheet_list|"):
        # Kembali ke daftar sheet dari file tertentu
        file_id = data.replace("back_to_sheet_list|", "")
        
        print(f"[DEBUG] User {username} going back to sheet list for file: {file_id}")
        
        # Check permission
        if not permission_service.has_file_permission(telegram_id, file_id, username):
            await query.answer("Access denied.", show_alert=True)
            return
        
        # Get file name
        file_name = context.user_data.get('selected_file_name', 'Unknown')
        
        # Get sheets using index service (lazy)
        from access_manager.services.spreadsheet_index_service import get_index_service
        index_service = get_index_service()
        indexed = index_service.get_or_index_file(file_id, file_name)
        
        if indexed:
            sheets = indexed.get_sheet_list()
            file_name = indexed.file_name
        else:
            sheets = gs.get_sheets_from_file(file_id)
        index_service.close()
        
        if not sheets:
            await query.edit_message_text("❌ Gagal mengambil daftar sheet dari file tersebut.")
            return
        
        # Clear selected sheet when going back to list
        context.user_data['selected_sheet_name'] = None
        
        keyboard = []
        for sheet_name in sheets:
            callback_data = encode_callback_data(f"sheet|{file_id}|{sheet_name}")
            keyboard.append([InlineKeyboardButton(sheet_name, callback_data=callback_data)])
        
        # Tambahkan tombol kembali ke daftar file
        keyboard.append([InlineKeyboardButton("← Kembali ke Daftar File", callback_data=encode_callback_data("back_to_files"))])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"📄 **Daftar Sheet**\n\n"
            f"File: {file_name}\n"
            f"Silakan pilih sheet yang ingin Anda lihat:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data == "back_to_files" or data == "back_to_root":
        # Kembali ke daftar file utama
        keyboard = []
        
        print(f"[DEBUG] User {username} going back to root files list")
        
        spreadsheet_files = gs.get_spreadsheet_files()
        
        if not spreadsheet_files:
            await query.edit_message_text("Tidak ada file spreadsheet yang ditemukan di folder.")
            return
        
        # Filter files based on user permissions
        for file in spreadsheet_files:
            file_id = file['id']
            file_name = file['name']
            
            # Check permission for this file/folder (pass username for fallback)
            has_permission = permission_service.has_file_permission(telegram_id, file_id, username)
            if not has_permission:
                continue
            
            # Tambahkan icon folder jika itu adalah folder
            if file.get('is_folder', False):
                display_name = f"[Folder] {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                # Tambahkan icon sheet jika itu adalah file spreadsheet
                parent_folder_name = file.get('parent_folder_name')
                if parent_folder_name:
                    display_name = f"[File] {file_name} (dari folder: {parent_folder_name})"
                else:
                    display_name = f"[File] {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        if not keyboard:
            print(f"[DEBUG] User {username} has no accessible files")
            await query.answer("Anda tidak memiliki akses ke file manapun.", show_alert=True)
            return
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "**Daftar File Spreadsheet dan Folder**\n\n"
            "Silakan pilih file atau folder yang ingin Anda lihat:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    username = update.effective_user.username
    
    print(f"[DEBUG] handle_message - User: {username} ({telegram_id})")
    
    # Check if user is registered in access manager
    session = get_session()
    try:
        # Try to find by telegram_id first, then fallback to username
        existing_user = session.query(TelegramUser).filter_by(telegram_id=telegram_id).first()
        if not existing_user and username:
            existing_user = session.query(TelegramUser).filter_by(username=username).first()
        
        if not existing_user:
            print(f"[DEBUG] Unregistered user {username} ({telegram_id}) tried to send message")
            await update.message.reply_text(
                "Maaf, Anda belum terdaftar dalam sistem. Silakan hubungi administrator untuk mendapatkan akses."
            )
            return
    finally:
        session.close()
    
    user_question = update.message.text.strip()
    if not user_question:
        return
    
    await update.message.chat.send_action(action="typing")
    
    # Cek apakah ada file/sheet yang sudah dipilih
    selected_file_id = context.user_data.get('selected_file_id')
    selected_sheet_name = context.user_data.get('selected_sheet_name')
    selected_file_name = context.user_data.get('selected_file_name', 'Unknown')
    
    print(f"DEBUG - selected_file_id: {selected_file_id}")
    print(f"DEBUG - selected_sheet_name: {selected_sheet_name}")
    
    # Prepare lowercase version for pattern matching
    user_question_lower = user_question.lower()
    
    # Check for search intent - these messages need spreadsheet data
    search_keywords = ['buka', 'cari', 'search', 'find', 'buka file', 'cari file', 'show', 'tampilkan', 'lihat', 'cek', 'apa', 'siapa', 'dimana', 'berapa', 'jumlah', 'total', 'list']
    has_search_intent = any(k in user_question_lower for k in search_keywords)
    
    print(f"[DEBUG] has_search_intent: {has_search_intent}, message: '{user_question}'")
    
    # Initialize variables
    sheet_str = None
    file_context = "Tidak ada file yang dipilih"
    
    if selected_file_id and selected_sheet_name:
        # User has selected a specific file/sheet - load that data
        print(f"[DEBUG] Loading data from selected file/sheet: {selected_file_name}/{selected_sheet_name}")
        raw_data = gs.get_sheet_data(selected_file_id, selected_sheet_name)
        file_context = f"File '{selected_file_name}', Sheet '{selected_sheet_name}'"
        
        if raw_data:
            # Convert 2D array ke string
            lines = []
            for row in raw_data[:20]:
                lines.append(" | ".join(str(c) for c in row))
            sheet_str = "\n".join(lines)
        else:
            sheet_str = "Data tidak ditemukan"
    elif selected_file_id and not selected_sheet_name:
        # File is selected but no sheet - auto-select sheets based on query
        print(f"[DEBUG] File '{selected_file_name}' selected but no sheet - auto-selecting based on query")
        
        # Use index service to get sheet names
        from access_manager.services.spreadsheet_index_service import get_index_service
        index_service = get_index_service()
        indexed = index_service.get_or_index_file(selected_file_id, selected_file_name)
        
        if indexed:
            all_sheets = indexed.get_sheet_list()
        else:
            all_sheets = gs.get_sheets_from_file(selected_file_id)
        index_service.close()
        
        # Find matching sheets based on query
        matching_sheets = []
        query_lower = user_question_lower
        
        for sheet_name in all_sheets:
            sheet_lower = sheet_name.lower()
            # Match if query keywords appear in sheet name
            if any(k in sheet_lower for k in query_lower.split() if len(k) > 2):
                matching_sheets.append(sheet_name)
        
        # If no match from keywords, try word-by-word matching
        if not matching_sheets:
            query_words = [w for w in query_lower.split() if len(w) > 2]
            for sheet_name in all_sheets:
                sheet_lower = sheet_name.lower()
                if any(word in sheet_lower for word in query_words):
                    matching_sheets.append(sheet_name)
        
        # Limit to reasonable number of sheets (max 5)
        matching_sheets = matching_sheets[:5]
        
        print(f"[DEBUG] Auto-selected {len(matching_sheets)} sheets: {matching_sheets}")
        
        # Load data from all matching sheets
        all_data_parts = []
        for sheet_name in matching_sheets:
            raw_data = gs.get_sheet_data(selected_file_id, sheet_name)
            if raw_data:
                all_data_parts.append(f"\n📄 Sheet: {sheet_name}")
                rows_to_show = min(10, len(raw_data))
                for i in range(rows_to_show):
                    if i == 0:
                        row_data = ' | '.join([str(cell) for cell in raw_data[i]])
                        all_data_parts.append(f"   Header: {row_data}")
                    else:
                        row_data = ' | '.join([str(cell) for cell in raw_data[i]])
                        all_data_parts.append(f"   {row_data}")
                if len(raw_data) > rows_to_show:
                    all_data_parts.append(f"   ... dan {len(raw_data) - rows_to_show} baris lainnya")
        
        if matching_sheets:
            file_context = f"File '{selected_file_name}' (auto-selected {len(matching_sheets)} sheet)"
            sheet_str = "\n".join(all_data_parts) if all_data_parts else "Data tidak ditemukan"
        else:
            file_context = f"File '{selected_file_name}' - tidak ada sheet yang cocok"
            sheet_str = f"Sheet tidak ditemukan. Sheet yang tersedia: {', '.join(all_sheets[:10])}"
    elif has_search_intent:
        # User asking about data - use index service for efficient search
        print(f"[DEBUG] Search intent detected, using index service")
        
        # Import here to avoid circular import
        from access_manager.services.spreadsheet_index_service import get_index_service
        
        # Extract search query
        search_query = None
        for keyword in search_keywords:
            if keyword in user_question_lower:
                idx = user_question_lower.find(keyword)
                query_after = user_question_lower[idx + len(keyword):].strip()
                query_after = query_after.replace('file', '').replace(':', '').strip()
                if query_after:
                    search_query = query_after
                    break
        
        # Use index service to find matching files (lazy loading)
        index_service = get_index_service()
        
        if search_query:
            print(f"[DEBUG] Searching index for: '{search_query}'")
            # Search by file name OR sheet name
            matching_indices = index_service.search_files(search_query)
            
            # Filter by user permissions
            accessible_indices = []
            for idx in matching_indices:
                if permission_service.has_file_permission(telegram_id, idx.file_id, username):
                    accessible_indices.append(idx)
            
            print(f"[DEBUG] Found {len(accessible_indices)} accessible files matching '{search_query}'")
            
            if not accessible_indices:
                await update.message.reply_text(
                    f"Tidak ada file yang cocok dengan '{search_query}'. Gunakan /start untuk melihat file yang tersedia."
                )
                index_service.close()
                return
            
            # Index and load only matching files (lazy)
            files_to_process = []
            for idx in accessible_indices:
                # Re-index if needed (will use cache if not modified)
                indexed = index_service.get_or_index_file(idx.file_id, idx.file_name)
                if indexed:
                    files_to_process.append(indexed)
            
            file_context = f"Ditemukan {len(files_to_process)} file yang cocok dengan '{search_query}'"
        else:
            # No specific query - show accessible files from index
            all_indices = index_service.get_all_indexed_files()
            
            # Filter by user permissions
            accessible_indices = []
            for idx in all_indices:
                if permission_service.has_file_permission(telegram_id, idx.file_id, username):
                    accessible_indices.append(idx)
            
            print(f"[DEBUG] User {username} - total accessible indexed files: {len(accessible_indices)}")
            
            if not accessible_indices:
                await update.message.reply_text(
                    "Anda tidak memiliki akses ke file manapun. Gunakan /start untuk memilih file."
                )
                index_service.close()
                return
            
            # Index files that user has access to (lazy)
            files_to_process = []
            for idx in accessible_indices:
                indexed = index_service.get_or_index_file(idx.file_id, idx.file_name)
                if indexed:
                    files_to_process.append(indexed)
            
            file_context = f"Total {len(files_to_process)} file yang dapat diakses"
        
        index_service.close()
        
        print(f"[DEBUG] Processing {len(files_to_process)} files")
        
        # Build data from files
        all_data_parts = []
        for idx in files_to_process:
            path_info = f" (Path: {idx.folder_path})" if idx.folder_path else ""
            all_data_parts.append(f"\n📁 File: {idx.file_name}{path_info}")
            
            sheets = idx.get_sheet_list()
            
            if not sheets:
                all_data_parts.append("   - Gagal mengambil sheet")
                continue
            
            for sheet_name in sheets:
                raw_data = gs.get_sheet_data(idx.file_id, sheet_name)
                
                if raw_data:
                    all_data_parts.append(f"   📄 Sheet: {sheet_name}")
                    rows_to_show = min(10, len(raw_data))
                    for i in range(rows_to_show):
                        if i == 0:
                            row_data = ' | '.join([str(cell) for cell in raw_data[i]])
                            all_data_parts.append(f"      Header: {row_data}")
                        else:
                            row_data = ' | '.join([str(cell) for cell in raw_data[i]])
                            all_data_parts.append(f"      {row_data}")
                    if len(raw_data) > rows_to_show:
                        all_data_parts.append(f"      ... dan {len(raw_data) - rows_to_show} baris lainnya")
                else:
                    all_data_parts.append(f"   - Sheet '{sheet_name}' kosong atau gagal dibaca")
        
        sheet_str = "\n".join(all_data_parts) if all_data_parts else "Data tidak ditemukan"
    else:
        # No specific file/sheet selected and no search intent
        # Just respond without loading spreadsheet data
        print(f"[DEBUG] No search intent - responding without spreadsheet data")
        sheet_str = "Tidak ada data yang dimuat. Gunakan /start untuk memilih file atau gunakan kata kunci seperti 'buka', 'cari', 'cek' untuk mencari data."
    
    # Gunakan instruksi format HTML
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
        # Langsung kirim dengan parse_mode HTML (tidak perlu escape)
        await update.message.reply_text(answer, parse_mode=TELEGRAM_PARSE_MODE)
    except Exception as e:
        print(f"Error AI: {e}")
        await update.message.reply_text("Maaf, terjadi kesalahan.")

def main():
    print("Memulai bot Telegram...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("sheets", sheets_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()