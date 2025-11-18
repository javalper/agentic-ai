import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

from .database.db_manager import DatabaseManager
from .agent.collection_agent import CollectionAgent
from .agent.learning_engine import LearningEngine
from .config.settings import settings

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description='Agentic AI - Alacak Yönetimi ve Yasal Takip Sistemi'
    )
    parser.add_argument(
        '--month',
        type=str,
        help='İşlenecek ay (YYYY-MM formatında)',
        default=None
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test modu'
    )
    parser.add_argument(
        '--analyze',
        action='store_true',
        help='Sistem performans analizi'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Çıktı dosyası yolu',
        default='collection_actions.json'
    )
    
    args = parser.parse_args()
    
    logger.info("Agentic AI Alacak Yönetimi Sistemi başlatılıyor...")
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        agent = CollectionAgent(session)
        learning_engine = LearningEngine(session)
        
        if args.analyze:
            logger.info("Sistem performans analizi yapılıyor...")
            performance = learning_engine.analyze_system_performance()
            
            print("\n" + "="*60)
            print("SİSTEM PERFORMANS ANALİZİ")
            print("="*60)
            print(f"Toplam Aksiyon: {performance['total_actions']}")
            print(f"Başarılı Aksiyon: {performance['successful_actions']}")
            print(f"Genel Başarı Oranı: {performance['overall_success_rate']:.2%}")
            print("\nKanal Bazlı Performans:")
            print("-"*60)
            
            for channel, stats in performance['channel_performance'].items():
                print(f"\n{channel.upper()}:")
                print(f"  Toplam Deneme: {stats['total_attempts']}")
                print(f"  Başarılı: {stats['successful_attempts']}")
                print(f"  Başarı Oranı: {stats['success_rate']:.2%}")
            
            print("="*60 + "\n")
            return
        
        logger.info("Vadesi geçmiş faturalar işleniyor...")
        actions = agent.process_overdue_invoices()
        
        logger.info(f"{len(actions)} yeni tahsilat aksiyonu oluşturuldu")
        
        report = agent.generate_action_report()
        
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Aksiyon raporu kaydedildi: {output_path}")
        
        print("\n" + "="*60)
        print("TAHSİLAT AKSİYON RAPORU")
        print("="*60)
        print(f"Tarih: {report['timestamp']}")
        print(f"Toplam Bekleyen Aksiyon: {report['total_pending_actions']}")
        print("\nKanal Bazlı Dağılım:")
        print("-"*60)
        
        for channel, count in report['actions_by_channel'].items():
            print(f"{channel.upper()}: {count} aksiyon")
        
        print("\nDetaylı Aksiyon Listesi:")
        print("-"*60)
        
        for action in report['actions'][:10]:
            print(f"\nAksiyon ID: {action['action_id']}")
            print(f"  Abone: {action['subscriber_name']} ({action['subscriber_number']})")
            print(f"  Fatura: {action['invoice_number']}")
            print(f"  Tutar: {action['amount_due']:.2f} TL")
            print(f"  Kanal: {action['channel']}")
            print(f"  Vade Geçme: {action['days_overdue']} gün")
            print(f"  Güven Skoru: {action['confidence_score']:.2%}")
        
        if len(report['actions']) > 10:
            print(f"\n... ve {len(report['actions']) - 10} aksiyon daha")
        
        print("="*60 + "\n")
        
        logger.info("İşlem tamamlandı")

if __name__ == '__main__':
    main()
