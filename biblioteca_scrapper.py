from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
import csv
import re
from bs4 import BeautifulSoup

FIELDS = [
    'Título', 'Autor', 'Filiación', 'Palabras clave', 'Año', 'Volumen', 'Número',
    'Página de inicio', 'Página de fin', 'DOI', 'Título revista', 'Título revista abreviado',
    'ISSN', 'CODEN', 'CAS', 'PDF','Registro'
]

session = requests.Session()
retries = Retry(
    total=5,  
    backoff_factor=1,  
    status_forcelist=[500, 502, 503, 504, 403], 
    allowed_methods=["GET"] 
)
session.mount("https://", HTTPAdapter(max_retries=retries))

def safe_request(url):
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status() 
        return response
    except requests.exceptions.SSLError as e:
        print(f"SSL Error: {e}. Retrying...")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return None

BASE_URL = "https://bibliotecadigital.exactas.uba.ar"
ROOT_URL = f"{BASE_URL}/collection/paper/browse/CL2"
LETTERS_RANGE = range(1, 26) 

csv_filename = "articles.csv"

def extract_urls(html):
    soup = BeautifulSoup(html, "lxml")
    links = soup.find_all("a", href=True)  
    valid_links = [link["href"] for link in links if link.text.strip() != "..."]  
    return valid_links


for letter_index in LETTERS_RANGE:
    letter_url = f"{ROOT_URL}/{letter_index}"
    letter_response = safe_request(letter_url)
    if (letter_response is None) or (letter_response.status_code != 200):
        print(f"Failed to retrieve {letter_url}")
        continue
    letter_soup = BeautifulSoup(letter_response.text, "html.parser")
    for author_link in letter_soup.find_all("a", href=True):
        author_href = author_link["href"]
        if not re.match(r"/collection/paper/browse/CL2/\d+/\d+", author_href):
            continue  
        author_url = f"{BASE_URL}{author_href}"
        author_response = safe_request(author_url)
        if (author_response is None) or (author_response.status_code != 200):
            print(f"Failed to retrieve {author_url}")
            continue
        author_soup = BeautifulSoup(author_response.text, "html.parser")

        for year_link in author_soup.find_all("a", href=True):
            year_href = year_link["href"]
            if not re.match(r"/collection/paper/browse/CL2/\d+/\d+/\d+", year_href):
                continue 
            year_url = f"{BASE_URL}{year_href}"
            year_response = safe_request(year_url)
            if year_response is None:
                print(f"Skipping {year_url} due to repeated failures.")
                continue
            year_soup = BeautifulSoup(year_response.text, "html.parser")

            for article_href in extract_urls(str(year_soup)):
                if not article_href.startswith("/collection/paper/document/"):
                    continue
                article_url = f"{BASE_URL}{article_href}"
                article_response = safe_request(article_url)
                if (article_response is None) or (article_response.status_code != 200):
                    print(f"Failed to retrieve {author_url}")
                    continue
                article_soup = BeautifulSoup(article_response.text, "html.parser")
                
                data = {field: '' for field in FIELDS} 
                for row in article_soup.find_all("tr"):
                    cells = row.find_all("td")
                    if len(cells) == 2:
                        key = cells[0].text.strip().replace(":", "")
                        value = cells[1].text.strip()
                        data[f"{key}"] = value

                with open(csv_filename, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.DictWriter(file, fieldnames=data.keys())
                    if file.tell() == 0:
                        writer.writeheader()
                    writer.writerow(data)
                print(f"Articulo: {data["Título"]} guardado")

print(f"listo. datos en {csv_filename}.")