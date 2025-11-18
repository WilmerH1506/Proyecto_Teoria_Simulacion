import psycopg2

def get_connection():
    """
    Retorna una conexión a la base de datos PostgreSQL.
    """
    try:
        conn = psycopg2.connect(
            host="localhost", # O la IP donde se ejecute Postgres
            database="Estados_Financieros",
            user="postgres",  # Tu usuario de Postgres
            password="admin123" # Tu contraseña
        )
        return conn
    except psycopg2.Error as e:
        print("Error al conectar a PostgreSQL:", e)
        return None