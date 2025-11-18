import sys
from pathlib import Path
import random

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.db_manager import DatabaseManager
from src.agent.collection_agent import CollectionAgent
from src.models.collection_action import ActionOutcome

def simulate_action_outcomes():
    print("Tahsilat aksiyonu sonuçları simüle ediliyor...")
    
    db_manager = DatabaseManager()
    
    with db_manager.get_session() as session:
        agent = CollectionAgent(session)
        
        pending_actions = agent.get_pending_actions()
        
        if not pending_actions:
            print("Simüle edilecek bekleyen aksiyon bulunamadı.")
            return
        
        print(f"{len(pending_actions)} bekleyen aksiyon bulundu")
        
        for action in pending_actions:
            success_probability = random.random()
            
            if success_probability > 0.7:
                outcome = ActionOutcome.SUCCESS
                amount_collected = action.amount_due
            elif success_probability > 0.5:
                outcome = ActionOutcome.PARTIAL_SUCCESS
                amount_collected = action.amount_due * random.uniform(0.3, 0.7)
            elif success_probability > 0.3:
                outcome = ActionOutcome.NO_RESPONSE
                amount_collected = 0.0
            else:
                outcome = ActionOutcome.FAILED
                amount_collected = 0.0
            
            agent.update_action_outcome(
                action.id,
                outcome,
                amount_collected
            )
            
            print(f"Aksiyon {action.id}: {outcome.value} - {amount_collected:.2f} TL tahsil edildi")
        
        print("\nSimülasyon tamamlandı!")
        print("Sistem öğrenme mekanizması güncellendi.")

if __name__ == '__main__':
    simulate_action_outcomes()
