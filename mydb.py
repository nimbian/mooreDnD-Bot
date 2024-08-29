import yaml
import psycopg2.pool
from contextlib import contextmanager

with open('config.yml', 'r') as f:
     CONFIG  = yaml.safe_load(f)

pool = psycopg2.pool.SimpleConnectionPool(16,32, user=CONFIG['psql']['user'],
                                               password=CONFIG['psql']['password'],
                                               host=CONFIG['psql']['ip'],
                                               port=CONFIG['psql']['port'],
                                               database=CONFIG['psql']['dbname'])


@contextmanager
def db_cursor():
    conn = pool.getconn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)
