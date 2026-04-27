from src.scraper import scrape_and_collect
from src.loader import load_to_db

def main():
    books_df, ranks_df = scrape_and_collect()
    load_to_db(books_df, ranks_df)

if __name__ == '__main__':
    main()