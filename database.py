from sqlalchemy import create_engine

db_url = "postgresql://postgres:Jennifer2004*@localhost:5432/fligth-database"

def get_engine():
    return create_engine(db_url)

def get_db_url():
    return db_url
    