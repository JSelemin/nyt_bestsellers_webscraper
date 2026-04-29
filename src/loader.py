import sqlite3
import pandas as pd

def load_to_db(books_df: pd.DataFrame, ranks_df: pd.DataFrame):

    conn = sqlite3.connect('./data/NYT_bestsellers.db')
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS books (
                hash_id TEXT PRIMARY KEY, 
                title TEXT, 
                author TEXT, 
                upc TEXT, 
                bookshop_url TEXT
                );
    
        CREATE TABLE IF NOT EXISTS ranks (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                hash_id TEXT NOT NULL REFERENCES books(hash_id), 
                date TEXT NOT NULL, 
                rank INTEGER NOT NULL, 
                UNIQUE(hash_id, date)
                );
            """)
    print("Database tables created or verified successfully.")

    books_records = books_df.to_dict(orient='records')
    cursor.executemany("""
        INSERT OR IGNORE INTO books (hash_id, title, author, upc, bookshop_url) 
                    VALUES (:hash_id, :title, :author, :upc, :bookshop_url)
    """, books_records)
    print("Books data inserted successfully.")

    ranks_records = ranks_df.to_dict(orient='records')
    cursor.executemany("""
        INSERT OR IGNORE INTO ranks (hash_id, date, rank) 
                    VALUES (:hash_id, :date, :rank)
    """, ranks_records)
    print("Ranks data inserted successfully.")

    conn.commit()
    print(f"Loaded {len(books_records)} books, {len(ranks_records)} ranks.")

    conn.close()