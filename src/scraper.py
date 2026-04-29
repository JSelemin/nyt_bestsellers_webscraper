import pandas as pd
import requests
import hashlib
import time
import sys
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

def generate_book_hash(title, author):

    input_string = f"{title.lower().strip()}|{author.lower().strip()}"
    return hashlib.md5(input_string.encode('utf-8')).hexdigest()

def get_books_ranks(sunday):

    link = f'https://www.nytimes.com/books/best-sellers/{sunday}/combined-print-and-e-book-fiction/'
    r = requests.get(link)
    date = sunday
    soup = BeautifulSoup(r.text, 'html.parser')

    results = soup.find_all("article", attrs={"class": "css-1u6k25n"})

    rank = 0
    ranks_data = []
    books_data = []

    for result in results: 
        author = result.find("p", attrs={"class": "css-hjukut"})
        title = result.find("h3", attrs={"class": "css-5pe77f"})
        rank += 1

        if author and title:
            author = author
            title = title.text
        else:
            print(f'Missing author or title for rank {rank} in {date}.')
            print("This is a critical error. Exiting the program.")
            author = None
            title = None
            sys.exit(1)

        raw_text = author.text.strip()
        if raw_text.lower().startswith("by "):
            clean_author = raw_text[3:].strip()
        else:
            clean_author = raw_text

        hash_id = generate_book_hash(title, clean_author)

        apple_books_tag = result.find("a", string="Apple Books") # type: ignore

        if apple_books_tag:
            bookshop_url = apple_books_tag.get('href')
            bookshop_url_clean = bookshop_url[:-10]
            upc = bookshop_url_clean[-13:]
        else:
            bookshop_url = None
            upc = None
            print(f'No Apple Books link found for {title} in {date}')
        
        ranks = {
            "hash_id": hash_id,
            "date": date,
            "rank": rank,
        }

        books = {
            "hash_id": hash_id,
            "title": title,
            "author": clean_author,
            "upc": upc,
            "bookshop_url": bookshop_url
        }

        books_data.append(books)
        ranks_data.append(ranks)
    return books_data, ranks_data

def scrape_and_collect(number_of_weeks: int):

    current = datetime.now()
    day_of_week = current.weekday()

    days_ahead = 6 - day_of_week
    day_sunday = current + timedelta(days=days_ahead)

    list_of_weeks = []

    for i in range(number_of_weeks):
        day_sunday = day_sunday - timedelta(weeks=1)
        list_of_weeks.append(day_sunday.strftime("%Y/%m/%d"))

    books_df = pd.DataFrame()
    ranks_df = pd.DataFrame()

    failed_weeks = []
    total_start_time = time.time()
    for i in list_of_weeks:
        start_time = time.time()
        try:
            books, ranks = get_books_ranks(i)
            new_books_df = pd.DataFrame(books)
            new_ranks_df = pd.DataFrame(ranks)
            
            books_df = pd.concat([books_df, new_books_df], axis=0)
            ranks_df = pd.concat([ranks_df, new_ranks_df], axis=0)
        except Exception as e:
            print(f"Failed {i}: {e}")
            failed_weeks.append(i)
            continue
        time.sleep(1.5)
        print(f"Finished week {i} in {time.time() - start_time:.2f} seconds")

    total_end_time = time.time() - total_start_time
    if failed_weeks == []:
        print(f"\nAll weeks scraped successfully in {total_end_time:.2f} seconds.")
    else:
        print(f"\nSomething went wrong. Failed weeks: {failed_weeks}, spent {total_end_time:.2f} seconds scraping.")

    books_df.drop_duplicates(subset=["hash_id"], inplace=True)
    books_df.reset_index(drop=True, inplace=True)
    ranks_df.reset_index(drop=True, inplace=True)

    return books_df, ranks_df