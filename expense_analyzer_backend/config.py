import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Database Configuration
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb://localhost:27017/finance_tracker'
    DATABASE_NAME = os.environ.get('DATABASE_NAME') or 'finance_tracker'
    
        # PostgreSQL Configuration for Reports
    SUPABASE_DB_URL = os.environ.get('SUPABASE_DB_URL')
    
    # JWT Configuration
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'jwt-secret-key-change-this'
    JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', 24))
    
    # API Configuration
    API_PREFIX = os.environ.get('API_PREFIX') or '/api/v1'
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001,http://localhost:8000').split(',')
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MONGO_URI = os.environ.get('TEST_MONGO_URI') or 'mongodb://localhost:27017/finance_tracker_test'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}