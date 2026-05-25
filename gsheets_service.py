import gspread
from google.oauth2.service_account import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = os.getenv("SHEET_NAME")

def get_all_data():
    """
    Mengambil semua data dari Google Sheets dan mengembalikannya sebagai string terformat.
    """
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 
                 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file('marine-bebop-275123-64b6d3ea1065.json', scopes=scope)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        data = sheet.get_all_values()
        
        if not data:
            return "Data kosong."
        
        header = data[0]
        rows = data[1:]
        
        formatted = f"📊 *Data dari sheet '{SHEET_NAME}':*\n\n"
        formatted += f"Kolom: {', '.join(header)}\n\n"
        
        for idx, row in enumerate(rows, start=1):
            formatted += f"**Baris {idx}:**\n"
            for col_name, cell_value in zip(header, row):
                formatted += f"  - {col_name}: {cell_value}\n"
            formatted += "\n"
        
        return formatted.strip()
    
    except Exception as e:
        print(f"Error membaca Google Sheets: {e}")
        return None