# services/sheets_service.py
import gspread
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def upload_to_sheets(df, config):
    """Sube datos a Google Sheets"""
    try:
        gc = gspread.service_account(filename='credentials.json')
        sh = gc.open(config['sheet_name'])
        
        sheet_name = datetime.now().strftime('%Y-%m-%d %H:%M')
        worksheet = sh.add_worksheet(title=sheet_name, rows="1000", cols="20")
        
        # Encabezados
        worksheet.append_row(df.columns.tolist())
        
        # Datos
        for row in df.values.tolist():
            worksheet.append_row(row)
        
        logger.info(f"Datos subidos a hoja '{sheet_name}'")
        
    except FileNotFoundError:
        logger.error("Archivo credentials.json no encontrado")
    except Exception as e:
        logger.error(f"Error al subir a Sheets: {e}")