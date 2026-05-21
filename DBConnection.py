import subprocess
from sqlalchemy import create_engine

DB_CONNECTION_STRING = "postgresql://postgres.clufdieovfbcyexdceea:{}@aws-1-us-west-1.pooler.supabase.com:5432/postgres"

def get_db_pass():
    result = subprocess.run(['pass', 'show', 'Password/Supabase'], capture_output=True, text=True)
    key = result.stdout.strip()
    return key

def get_db_connection():
    connection_string = DB_CONNECTION_STRING.format(get_db_pass())
    engine = create_engine(connection_string, connect_args={"sslmode": "require"})
    return engine
