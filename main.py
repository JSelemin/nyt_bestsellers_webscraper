from src.scraper import scrape_and_collect
from src.loader import load_to_db

weeks_to_scrape = 152

def main():
    books_df, ranks_df = scrape_and_collect(weeks_to_scrape)
    load_to_db(books_df, ranks_df)

if __name__ == '__main__':
    main()