import sqlite3
import pandas as pd

def load_to_db(books_df: pd.DataFrame, ranks_df: pd.DataFrame):

    conn = sqlite3.connect('./data/raw/NYT_bestsellers.db')
    cursor = conn.cursor()

    books_df.to_sql('books', conn, if_exists="replace", )
    ranks_df.to_sql('ranks', conn, if_exists="replace")

    conn.close()