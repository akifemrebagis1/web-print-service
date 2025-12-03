"""
Uygulama yapılandırma ayarları.
Environment variable'lardan veya varsayılan değerlerden konfigürasyon yükler.
"""

import os
from pathlib import Path


class Config:
    """Temel uygulama konfigürasyonu."""

    # Proje kök dizini
    BASE_DIR = Path(__file__).resolve().parent

    # Flask ayarları
    SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.environ.get(
        'FLASK_DEBUG', 'False').lower() in ('true', '1', 'yes')

    # Upload ayarları
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    TEMPLATES_FOLDER = os.environ.get(
        'TEMPLATES_FOLDER', str(BASE_DIR / 'templates'))
    MAX_CONTENT_LENGTH = int(os.environ.get(
        'MAX_CONTENT_LENGTH', 100 * 1024 * 1024))  # 100MB

    # İzin verilen dosya uzantıları
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff'}

    # Sunucu ayarları
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))

    # Tarayıcı otomatik açma (üretim ortamında kapalı olmalı)
    AUTO_OPEN_BROWSER = os.environ.get(
        'AUTO_OPEN_BROWSER', 'False').lower() in ('true', '1', 'yes')


class DevelopmentConfig(Config):
    """Geliştirme ortamı konfigürasyonu."""
    DEBUG = True
    AUTO_OPEN_BROWSER = True


class ProductionConfig(Config):
    """Üretim ortamı konfigürasyonu."""
    DEBUG = False
    AUTO_OPEN_BROWSER = False


class TestingConfig(Config):
    """Test ortamı konfigürasyonu."""
    TESTING = True
    DEBUG = True


# Ortam bazlı konfigürasyon seçimi
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Ortam değişkenine göre konfigürasyon döndürür."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_by_name.get(env, config_by_name['default'])
