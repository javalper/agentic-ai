import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager
from src.models.subscriber import Subscriber, AgeGroup, IncomeLevel
from src.models.invoice import Invoice, InvoiceStatus
from src.models.payment_history import PaymentHistory
from src.models.collection_action import CollectionAction, CollectionChannel, ActionOutcome

def load_sample_data():
    print("Örnek veri yükleniyor...")
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        existing_count = session.query(Subscriber).count()
        if existing_count > 0:
            print(f"Uyarı: Veritabanında zaten {existing_count} abone var.")
            print("Mevcut veriyi korumak için yükleme iptal ediliyor.")
            print("Veritabanını sıfırlamak için: python -m src.scripts.init_db --reset")
            return
        
        subscribers_data = [
            {
                'subscriber_number': 'SUB001',
                'name': 'Ahmet Yılmaz',
                'phone': '+905551234567',
                'email': 'ahmet.yilmaz@example.com',
                'age_group': AgeGroup.MIDDLE,
                'income_level': IncomeLevel.MEDIUM,
                'region': 'İstanbul',
                'payment_reliability_score': 0.8,
                'average_days_late': 2.5,
                'total_invoices': 12,
                'paid_on_time_count': 10,
                'paid_late_count': 2,
                'unpaid_count': 0
            },
            {
                'subscriber_number': 'SUB002',
                'name': 'Ayşe Demir',
                'phone': '+905559876543',
                'email': 'ayse.demir@example.com',
                'age_group': AgeGroup.YOUNG,
                'income_level': IncomeLevel.LOW,
                'region': 'Ankara',
                'payment_reliability_score': 0.4,
                'average_days_late': 15.0,
                'total_invoices': 10,
                'paid_on_time_count': 3,
                'paid_late_count': 5,
                'unpaid_count': 2
            },
            {
                'subscriber_number': 'SUB003',
                'name': 'Mehmet Kaya',
                'phone': '+905557654321',
                'email': 'mehmet.kaya@example.com',
                'age_group': AgeGroup.SENIOR,
                'income_level': IncomeLevel.HIGH,
                'region': 'İzmir',
                'payment_reliability_score': 0.95,
                'average_days_late': 0.5,
                'total_invoices': 24,
                'paid_on_time_count': 23,
                'paid_late_count': 1,
                'unpaid_count': 0
            },
            {
                'subscriber_number': 'SUB004',
                'name': 'Fatma Şahin',
                'phone': '+905553456789',
                'email': 'fatma.sahin@example.com',
                'age_group': AgeGroup.ELDERLY,
                'income_level': IncomeLevel.MEDIUM,
                'region': 'Bursa',
                'payment_reliability_score': 0.6,
                'average_days_late': 8.0,
                'total_invoices': 18,
                'paid_on_time_count': 10,
                'paid_late_count': 7,
                'unpaid_count': 1
            },
            {
                'subscriber_number': 'SUB005',
                'name': 'Ali Özkan',
                'phone': '+905558765432',
                'email': 'ali.ozkan@example.com',
                'age_group': AgeGroup.YOUNG,
                'income_level': IncomeLevel.MEDIUM,
                'region': 'Antalya',
                'payment_reliability_score': 0.3,
                'average_days_late': 25.0,
                'total_invoices': 8,
                'paid_on_time_count': 2,
                'paid_late_count': 3,
                'unpaid_count': 3
            }
        ]
        
        subscribers = []
        for data in subscribers_data:
            subscriber = Subscriber(**data)
            session.add(subscriber)
            subscribers.append(subscriber)
        
        session.flush()
        
        print(f"{len(subscribers)} abone eklendi")
        
        invoices = []
        now = datetime.utcnow()
        
        for subscriber in subscribers:
            for i in range(3):
                issue_date = now - timedelta(days=60 - i*30)
                due_date = issue_date + timedelta(days=15)
                
                amount = random.uniform(150, 500)
                
                days_overdue = (now - due_date).days
                
                if days_overdue > 0:
                    status = InvoiceStatus.OVERDUE
                    paid_amount = 0.0
                else:
                    status = InvoiceStatus.PENDING
                    paid_amount = 0.0
                
                if subscriber.payment_reliability_score > 0.7 and i < 2:
                    status = InvoiceStatus.PAID
                    paid_amount = amount
                    payment_date = due_date - timedelta(days=random.randint(0, 5))
                elif subscriber.payment_reliability_score < 0.5 and days_overdue > 10:
                    status = InvoiceStatus.OVERDUE
                    paid_amount = 0.0
                
                invoice = Invoice(
                    invoice_number=f'INV-{subscriber.subscriber_number}-{i+1:03d}',
                    subscriber_id=subscriber.id,
                    amount=amount,
                    paid_amount=paid_amount,
                    remaining_amount=amount - paid_amount,
                    issue_date=issue_date,
                    due_date=due_date,
                    payment_date=payment_date if status == InvoiceStatus.PAID else None,
                    status=status,
                    billing_period_start=issue_date - timedelta(days=30),
                    billing_period_end=issue_date
                )
                session.add(invoice)
                invoices.append(invoice)
        
        session.flush()
        
        print(f"{len(invoices)} fatura eklendi")
        
        paid_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.PAID]
        for invoice in paid_invoices:
            payment = PaymentHistory(
                invoice_id=invoice.id,
                subscriber_id=invoice.subscriber_id,
                amount=invoice.paid_amount,
                payment_date=invoice.payment_date,
                payment_method='Banka Transferi',
                days_after_due=0 if invoice.payment_date <= invoice.due_date else (invoice.payment_date - invoice.due_date).days
            )
            session.add(payment)
        
        print(f"{len(paid_invoices)} ödeme kaydı eklendi")
        
        overdue_invoices = [inv for inv in invoices if inv.status == InvoiceStatus.OVERDUE]
        sample_actions = []
        
        for invoice in overdue_invoices[:5]:
            days_overdue = invoice.days_overdue()
            
            if days_overdue <= 7:
                channel = CollectionChannel.SMS
            elif days_overdue <= 14:
                channel = CollectionChannel.IVR
            elif days_overdue <= 30:
                channel = CollectionChannel.CALL_CENTER
            else:
                channel = CollectionChannel.DEBT_COLLECTION_CENTER
            
            action = CollectionAction(
                invoice_id=invoice.id,
                subscriber_id=invoice.subscriber_id,
                channel=channel,
                action_date=now - timedelta(days=random.randint(1, 5)),
                days_overdue_at_action=days_overdue,
                amount_due=invoice.remaining_amount,
                outcome=ActionOutcome.PENDING,
                ai_confidence_score=random.uniform(0.6, 0.95),
                decision_factors='{"days_overdue": ' + str(days_overdue) + ', "reliability_score": 0.5}'
            )
            session.add(action)
            sample_actions.append(action)
        
        print(f"{len(sample_actions)} örnek tahsilat aksiyonu eklendi")
        
        session.commit()
        
        print("\nÖrnek veri başarıyla yüklendi!")
        print(f"Toplam Abone: {len(subscribers)}")
        print(f"Toplam Fatura: {len(invoices)}")
        print(f"Vadesi Geçmiş Fatura: {len(overdue_invoices)}")
        print(f"Ödenen Fatura: {len(paid_invoices)}")

if __name__ == '__main__':
    load_sample_data()
