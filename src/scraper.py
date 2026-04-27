import pandas as pd
import requests
import hashlib
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
        title = result.find("h3", attrs={"class": "css-5pe77f"}).text
        rank += 1

        raw_text = author.text.strip()
        if raw_text.lower().startswith("by "):
            clean_author = raw_text[3:].strip()
        else:
            clean_author = raw_text

        hash_id = generate_book_hash(title, clean_author)

        bookshop_url = result.find("a", string="Apple Books", attrs={"class": "css-114t425"}).get('href')
        bookshop_url_clean = bookshop_url[:-10]
        upc = bookshop_url_clean[-13:]
        
        ranks = {
            "hash_id": hash_id,
            "date": date,
            "rank": rank,
            "upc": upc
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

    
def scrape_and_collect():

    current = datetime.now()
    day_of_week = current.weekday()

    days_ahead = 6 - day_of_week
    next_sunday = current + timedelta(days=days_ahead)

    print(current.strftime("%Y/%m/%d"))
    print(next_sunday.strftime("%Y/%m/%d"))

    list_of_weeks = []
    previous_sunday = next_sunday

    for i in range(5):
        previous_sunday = previous_sunday - timedelta(weeks=1)
        list_of_weeks.append(previous_sunday.strftime("%Y/%m/%d"))

    books_df = pd.DataFrame()
    ranks_df = pd.DataFrame()

    for i in list_of_weeks:
        books, ranks = get_books_ranks(i)
        new_books_df = pd.DataFrame(books)
        new_ranks_df = pd.DataFrame(ranks)
        
        books_df = pd.concat([books_df, new_books_df], axis=0)
        ranks_df = pd.concat([ranks_df, new_ranks_df], axis=0)

    books_df.drop_duplicates(subset=["hash_id"], inplace=True)
    books_df.reset_index(drop=True, inplace=True)
    ranks_df.reset_index(drop=True, inplace=True)

    return books_df, ranks_df