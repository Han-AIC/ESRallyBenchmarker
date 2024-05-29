import requests
from requests.exceptions import HTTPError, RequestException
from bs4 import BeautifulSoup
import requests 
import re
from tqdm import tqdm
import logging
import csv
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Webscraper:
    @staticmethod
    def fetch_html(url):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/' 
        }
        session = requests.Session()
        try:
            response = session.get(url, headers=headers)
            response.raise_for_status()
            document={"content":response.text, "url":url}
            return document
        
        except requests.exceptions.MissingSchema:
            logger.error(f"Invalid URL (no schema): {url}")
            raise ValueError("Invalid URL: No schema supplied. Perhaps you meant 'http://' or 'https://'.")
        except requests.exceptions.InvalidURL:
            logger.error(f"Invalid URL (malformed): {url}")
            raise ValueError("Invalid URL: The URL is malformed.")
        except HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            if response.status_code == 403:
                raise HTTPError(f"HTTP 403 Forbidden error: {http_err}. You might be blocked.")
            else:
                raise HTTPError(f"HTTP error occurred: {http_err}")
        except RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
            raise RequestException(f"Request error occurred: {req_err}")
        
class WikipediaDataProcessor:

    @staticmethod
    def extract_infobox(soup):
        infobox_data=[]   
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            for row in infobox.find_all('tr'):
                header = row.find('th')
                if header:
                    key = header.get_text(strip=True)
                    value = row.find('td')
                    if value:
                        infobox_data.append(f'{key}: {value.get_text(strip=False)}')
        if len(infobox_data)>0:
            return '\n'.join(infobox_data)
        else:
            return 'No Infobox'

    @staticmethod
    def extract_urls_structure(soup):
        urls=[]
        for a in soup.find_all('a', href=True):
            href = a['href']
            if re.match(r'^/wiki/', href):  # Restricting to Wikipedia article links
                full_url = f"https://en.wikipedia.org{href}"
                link_text = a.get_text(strip=True)
                # Filter out non-article URLs
                filter_pattern = r'^https://en\.wikipedia\.org/wiki/(Wikipedia:|Portal:|Special:|Help:|File:|Category:|Talk:|Template:|Template_talk:|Main_Page|#)'
                if not re.match(filter_pattern, full_url):
                    urls.append(full_url)
        return urls
    
    @staticmethod
    def extract_article_content(soup):
        def clean_text(text):
            text = text.replace('\\', '')
            text = text.replace('\n', ' ')
            pattern = r'\[.*?\]'
            cleaned_text = re.sub(pattern, ' ', text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
            cleaned_text = re.sub(r'(\w)\s+(\w)', r'\1 \2', cleaned_text)
            return cleaned_text 

        # Extract the title
        title = clean_text(soup.find('h1', {'id': 'firstHeading'}).get_text(strip=False))

        # Extract the introduction
        intro_paragraphs = []
        for p in soup.select('div.mw-parser-output > p'):
            if p.find_previous_sibling(['h2', 'h3', 'h4', 'h5', 'h6']):
                break
            text=clean_text(p.get_text(strip=False))
            intro_paragraphs.append(text)

        # Extract the main content sections
        sections = []
        for header in soup.select('h2, h3'):
            section_title = clean_text(header.get_text(strip=False))

            filter_pattern = r'Contents|See also|References|External links'
            if not re.match(filter_pattern, section_title):
                section_content = []
                for sibling in header.find_next_siblings():
                    if sibling.name and sibling.name.startswith('h'):
                        break
                    if sibling.name in ['p', 'ul', 'ol']:
                        text=clean_text(sibling.get_text(strip=False))
                        section_content.append(text)
                sections.append({
                    'title': section_title,
                    'content': ' '.join(section_content)
                })

        return {
            'title': title,
            'content': ' '.join(intro_paragraphs),
            'sections': sections
        }

class DocumentController:
    @staticmethod
    def create_document_object(url, contents, infobox):
        doc_obj = {'title':contents['title'],
                'introduction':contents['content'], 
                'infobox':infobox,
                'url':url,
                'article':'\n'.join(['\n'.join([i['title'], i['content']]) for i in contents['sections']])}
        return doc_obj
    
    @staticmethod
    def save_dicts_to_csv(dict_list, filename):
        if not dict_list:
            raise ValueError("The list of dictionaries is empty.")
        headers = dict_list[0].keys()
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for data in dict_list:
                writer.writerow(data)
        
        
class Scraper:
    def __init__(self):
        self.ws = Webscraper() 
        self.wdp = WikipediaDataProcessor()
        self.dc = DocumentController()

    def scrape(self, url):
        webdoc = self.ws.fetch_html(url)
        soup = BeautifulSoup(webdoc['content'], 'html.parser')
        urls=self.wdp.extract_urls_structure(soup)
        contents=self.wdp.extract_article_content(soup)
        infobox=self.wdp.extract_infobox(soup)
        document_obj=self.dc.create_document_object(url, contents, infobox)
        return urls, document_obj
    
    def scrape_with_depth(self, url, max_depth=2, max_docs=100):
        visited = set()
        documents = []

        def scrape_recursive(current_url, current_depth, pbar):
            if current_depth > max_depth or current_url in visited or len(documents) >= max_docs:
                return
            visited.add(current_url)
            
            try:
                urls, document_obj = self.scrape(current_url)
                documents.append(document_obj)
                pbar.update(1)  # Update progress bar after adding a document
                
                # Filter out visited URLs
                novel_urls = [url for url in urls if url not in visited]
                
                if not novel_urls:
                    return  # Terminate recursion if no new URLs to visit

                for url in novel_urls:
                    if len(documents) >= max_docs:
                        break
                    scrape_recursive(url, current_depth + 1, pbar)
            except Exception as e:
                print(f"Failed to scrape {current_url}: {e}")

        with tqdm(total=max_docs, desc="Scraping Progress", unit="doc") as pbar:
            scrape_recursive(url, 0, pbar)
        
        return documents

