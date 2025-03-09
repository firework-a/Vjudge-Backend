# app/core/tortoise_orm_config
from app.core.config import settings

TORTOISE_ORM = {
        'connections': {
            'default': {
                'engine': 'tortoise.backends.mysql',
                'credentials': {
                    'host': settings.DB_HOST,
                    'port': settings.DB_PORT,
                    'user': settings.DB_USERNAME,
                    'password': settings.DB_PASSWORD,
                    'database': settings.DB_NAME,
                    'minsize': 1,
                    'maxsize': 10,
                    'charset': 'utf8mb4',
                    'echo': True,  # 开发环境可以保留，生产环境建议关闭
                }
            }
        },
        'apps': {
            'models': {
                'models': ['app.models', 'aerich.models'],
                'default_connection': 'default',
            }
        },
        'use_tz': True,  # 启用时区支持
        'time_zone': '+08:00',  # 设置时区
    }