import subprocess
from sqlalchemy import create_engine, URL

def get_db_pass():
    result = subprocess.run(['pass', 'show', 'Password/Supabase'], capture_output=True, text=True, check=True)
    key = result.stdout.strip()
    return key

def get_db_connection():
    connection_url = URL.create(
        'postgresql+psycopg2',
        username='postgres.clufdieovfbcyexdceea',
        password=get_db_pass(),
        host='aws-1-us-west-1.pooler.supabase.com',
        port=5432,
        database='postgres'
    )

    engine = create_engine(connection_url, connect_args={"sslmode": "require"})
    return engine
