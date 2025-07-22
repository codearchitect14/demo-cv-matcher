def get_all_jobs(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM jobs")
        return cur.fetchall()
