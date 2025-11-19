import sys
import argparse
import os
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager

def init_database(reset=False):
    db_manager = DatabaseManager()
    
    print(f"Veritabanı konumu: {db_manager.engine.url}")
    
    if reset:
        print("Mevcut veritabanı temizleniyor...")
        
        db_url_str = str(db_manager.engine.url)
        if db_url_str.startswith('sqlite:///'):
            db_file = db_url_str.replace('sqlite:///', '')
            if db_file.startswith('./'):
                db_file = db_file[2:]
            
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"Veritabanı dosyası silindi: {db_file}")
        else:
            db_manager.drop_tables()
            print("Tablolar silindi")
    
    print("Veritabanı tabloları oluşturuluyor...")
    db_manager.create_tables()
    
    print("Veritabanı başarıyla oluşturuldu!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Initialize database tables')
    parser.add_argument('--reset', action='store_true', 
                       help='Drop existing tables/database before creating new ones')
    
    args = parser.parse_args()
    init_database(reset=args.reset)
