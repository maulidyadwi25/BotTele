import asyncio
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import gsheets_service as gs
from ai_service import get_ai_provider
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_PARSE_MODE = os.getenv("TELEGRAM_PARSE_MODE", "HTML")  # default HTML
ai_provider = get_ai_provider()
print(f"AI Provider aktif: {os.getenv('AI_PROVIDER')}")

# Cache data sheet
data_cache = {"content": None, "timestamp": 0}
CACHE_DURATION = 60

def get_sheet_data():
    global data_cache
    now = time.time()
    if data_cache["content"] is None or now - data_cache["timestamp"] > CACHE_DURATION:
        data_cache["content"] = gs.get_all_data()
        data_cache["timestamp"] = now
    return data_cache["content"]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo! Saya adalah bot yang bisa membaca data dari Google Sheets.\n\n"
        "Kirim pertanyaan seperti:\n"
        "- 'Tolong jelaskan baris 1'\n"
        "- 'Apa isi kolom Nama di baris 3?'\n"
        "- 'Tampilkan semua data'\n\n"
        "Saya akan menjawab berdasarkan data di spreadsheet Anda."
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
    
    # Gunakan instruksi format HTML
    system_prompt = f"""
    Anda adalah asisten yang membantu menjawab pertanyaan berdasarkan data berikut.
    Data dari Google Sheets:
    {sheet_data}

    **PENTING: Format Jawaban**
    - Format jawaban menggunakan sintaks **HTML** yang didukung Telegram.
    - Gunakan tag: <b>teks tebal</b>, <i>teks miring</i>, <u>garis bawah</u>, <code>kode</code>, <pre>blok kode</pre>.
    - Untuk daftar, gunakan karakter - atau * di awal baris (tanpa tag HTML).
    - Pisahkan bagian dengan baris kosong.
    - Jangan gunakan markdown (seperti * atau _).
    - Jangan sertakan karakter < atau > di luar tag HTML.
    - Jawab pertanyaan pengguna dengan jelas dan akurat berdasarkan data di atas.
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()