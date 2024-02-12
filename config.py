class config:
    SECRET_KEY = 'B!weNAt1T´%kvhUI*S'
    
class DevelopmentConfig(config):
    DEBUG=True
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'greensoftworld'
    
config ={
    'development': DevelopmentConfig
}