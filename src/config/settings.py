import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./receivables.db')
    
    LEARNING_RATE = float(os.getenv('LEARNING_RATE', '0.1'))
    MIN_CONFIDENCE_THRESHOLD = float(os.getenv('MIN_CONFIDENCE_THRESHOLD', '0.6'))
    
    SMS_DAYS_THRESHOLD = int(os.getenv('SMS_DAYS_THRESHOLD', '7'))
    IVR_DAYS_THRESHOLD = int(os.getenv('IVR_DAYS_THRESHOLD', '14'))
    CALL_CENTER_DAYS_THRESHOLD = int(os.getenv('CALL_CENTER_DAYS_THRESHOLD', '30'))
    
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'receivables_ai.log')
    
    CHANNEL_WEIGHTS = {
        'payment_reliability': 0.3,
        'days_overdue': 0.25,
        'historical_success': 0.25,
        'demographic': 0.2
    }
    
    DEMOGRAPHIC_PREFERENCES = {
        'YOUNG': ['sms', 'ivr'],
        'MIDDLE': ['ivr', 'call_center'],
        'SENIOR': ['call_center', 'ivr'],
        'ELDERLY': ['call_center']
    }
    
    INCOME_LEVEL_THRESHOLDS = {
        'LOW': 0.7,
        'MEDIUM': 0.5,
        'HIGH': 0.3
    }

settings = Settings()
