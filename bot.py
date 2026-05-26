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
    keyboard = []
    
    # Ambil daftar file spreadsheet dan folder
    spreadsheet_files = gs.get_spreadsheet_files()
    
    if not spreadsheet_files:
        await update.message.reply_text("❌ Tidak ada file spreadsheet yang ditemukan di folder.")
        return
    
    # Buat button untuk setiap file dan folder
    for file in spreadsheet_files:
        file_id = file['id']
        file_name = file['name']
        
        # Tambahkan icon folder jika itu adalah folder
        if file.get('is_folder', False):
            display_name = f"📁 {file_name}"
            callback_data = encode_callback_data(f"folder_{file_id}")
        else:
            # Tambahkan icon sheet jika itu adalah file spreadsheet
            parent_folder_name = file.get('parent_folder_name')
            if parent_folder_name:
                display_name = f"📄 {file_name} (dari folder: {parent_folder_name})"
            else:
                display_name = f"📄 {file_name}"
            callback_data = encode_callback_data(f"file_{file_id}")
        
        keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
    
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
    
    if data.startswith("folder_"):
        # User memilih folder, tampilkan isi folder tersebut
        folder_id = data.split("_", 1)[1]
        
        # Simpan folder ID saat ini di user_data
        context.user_data['current_folder_id'] = folder_id
        
        # Ambil daftar file dan folder dalam folder tersebut
        files = gs.get_files_in_folder(folder_id)
        
        if not files:
            await query.edit_message_text("❌ Folder ini kosong atau tidak dapat diakses.")
            return
        
        keyboard = []
        for file in files:
            file_id = file['id']
            file_name = file['name']
            
            # Tambahkan icon folder jika itu adalah folder
            if file.get('is_folder', False):
                display_name = f"📁 {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                # Tambahkan icon sheet jika itu adalah file spreadsheet
                display_name = f"📄 {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
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
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Tambahkan timestamp dan random number untuk membuat konten unik
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        folder_num = len(files)
        
        # Buat deskripsi folder yang unik
        folder_desc = f"📂 **Isi Folder** ({folder_num} item)\n"
        folder_desc += f"📂 ID: {folder_id[:8]}...\n"
        folder_desc += f"⏱️ {timestamp}-{random_num}\n\n"
        folder_desc += f"Silakan pilih file atau folder yang ingin Anda lihat:"
        
        await query.edit_message_text(
            folder_desc,
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )
    
    elif data.startswith("file_"):
        # User memilih file, tampilkan daftar sheet
        file_id = data.split("_", 1)[1]
        
        # Ambil nama file
        file_name = gs.get_file_name(file_id)
        
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
        
        # Debug: print apa yang diterima
        print(f"DEBUG callback data: {data}")
        print(f"DEBUG decoded: {data_decoded}")
        print(f"DEBUG parts: {parts}")
        print(f"DEBUG file_id: {file_id}, sheet_name: {sheet_name}")
        
        # Simpan informasi sheet untuk digunakan nanti
        context.user_data['selected_file_id'] = file_id
        context.user_data['selected_sheet_name'] = sheet_name
        
        # Tampilkan pilihan aksi
        keyboard = [
            [InlineKeyboardButton("📋 Ambil Data Lengkap", callback_data=encode_callback_data(f"action|data|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("📊 Hitung Rata-rata", callback_data=encode_callback_data(f"action|avg|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("🔢 Hitung Total", callback_data=encode_callback_data(f"action|total|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("📈 Statistik", callback_data=encode_callback_data(f"action|stats|{file_id}|{sheet_name}"))],
            [InlineKeyboardButton("← Kembali ke Daftar Sheet", callback_data=encode_callback_data(f"file|{file_id}"))]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📄 **Sheet: {sheet_name}**\n\n"
            f"Pilih aksi yang ingin Anda lakukan:",
            reply_markup=reply_markup,
            parse_mode=TELEGRAM_PARSE_MODE
        )

    elif data.startswith("action|"):
        # User memilih aksi untuk sheet
        parts = data.replace("action|", "action|").split("|")
        action_type = parts[1]
        file_id = parts[2]
        sheet_name = parts[3]
        
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
            
            # Tambahkan tombol kembali
            keyboard = [[InlineKeyboardButton("← Kembali ke Pilihan Aksi", callback_data=encode_callback_data(f"sheet|{file_id}|{sheet_name}"))]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                output,
                reply_markup=reply_markup,
                parse_mode=TELEGRAM_PARSE_MODE
            )
            
        except Exception as e:
            print(f"Error getting sheet data: {e}")
            await query.edit_message_text(f"❌ Gagal mengambil data dari sheet: {str(e)}")
    
    elif data == "back_to_files" or data == "back_to_root":
        # Kembali ke daftar file utama
        keyboard = []
        
        spreadsheet_files = gs.get_spreadsheet_files()
        
        if not spreadsheet_files:
            await query.edit_message_text("❌ Tidak ada file spreadsheet yang ditemukan di folder.")
            return
        
        for file in spreadsheet_files:
            file_id = file['id']
            file_name = file['name']
            
            # Tambahkan icon folder jika itu adalah folder
            if file.get('is_folder', False):
                display_name = f"📁 {file_name}"
                callback_data = encode_callback_data(f"folder_{file_id}")
            else:
                # Tambahkan icon sheet jika itu adalah file spreadsheet
                parent_folder_name = file.get('parent_folder_name')
                if parent_folder_name:
                    display_name = f"📄 {file_name} (dari folder: {parent_folder_name})"
                else:
                    display_name = f"📄 {file_name}"
                callback_data = encode_callback_data(f"file_{file_id}")
            
            keyboard.append([InlineKeyboardButton(display_name, callback_data=callback_data)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📂 **Daftar File Spreadsheet dan Folder**\n\n"
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
        await update.message.reply_text("❌ Gagal mengambil data dari Google Sheets.")
        return
    
    # Cek apakah ada file/sheet yang sudah dipilih
    selected_file_id = context.user_data.get('selected_file_id')
    selected_sheet_name = context.user_data.get('selected_sheet_name')
    selected_file_name = context.user_data.get('selected_file_name', 'Unknown')
    
    print(f"DEBUG - selected_file_id: {selected_file_id}")
    print(f"DEBUG - selected_sheet_name: {selected_sheet_name}")
    
    if selected_file_id and selected_sheet_name:
        # Ambil data hanya dari sheet yang dipilih
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
    else:
        # Fallback ke seluruh folder
        raw_data = get_sheet_data()
        file_context = "Seluruh folder Google Drive"
        
        # Data dari get_sheet_data adalah string, langsung gunakan
        sheet_str = raw_data if raw_data else "Data tidak ditemukan"
    
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