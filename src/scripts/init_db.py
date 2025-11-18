import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager

def init_database():
    print("Veritabanı oluşturuluyor...")
    
    db_manager = DatabaseManager()
    
    db_manager.create_tables()
    
    print("Veritabanı başarıyla oluşturuldu!")
    print(f"Veritabanı konumu: {db_manager.engine.url}")

if __name__ == '__main__':
    init_database()
