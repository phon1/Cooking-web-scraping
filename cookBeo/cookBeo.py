import requests
from bs4 import BeautifulSoup
import json
import os
import threading
import time

MAX_RETRIES = 3


count_id = 1
data = []
lock = threading.Lock() 

main_url = 'https://cookbeo.com/recipes/'

def response(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup

def get_links_from_page(url):
    soup = response(url)
    links = []
    for li in soup.find_all('li', class_='category'):
        link = li.a.get('href')
        links.append(link)
    return links

def get_link_content_cook(category_link):
    list_links = []

    soup = response(category_link)
    list_div_spotlight = soup.find('div', class_ = 'spotlight')
    list_div_class_list_style2 = soup.find('div', class_ = 'list-style2')

    if list_div_class_list_style2:
        for a in list_div_class_list_style2.find_all('a'):
            link = a.get('href')
            list_links.append(link)

    if list_div_spotlight:
        for a in list_div_spotlight.find_all('a'):
            link = a.get('href')
            list_links.append(link)
    return list_links   


def is_link_duplicate(link):
    if os.path.exists("cookBeo.json"):
        with open("cookBeo.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
            for entry in data:
                if entry.get("link") == link:
                    return True
    return False

def get_content(link):
    if is_link_duplicate(link):
        print(f'Data exists at Link: {link}\n') 
    else:
        print(f'--Get content: {link}--\n') 
     
        soup = response(link)
        article_content = soup.find('article', class_='post-content')
        global count_id
        id = count_id
        if article_content:
            title = article_content.find('h1').text.strip()
            content =  article_content.text.strip().replace(title, '')
            # Thực hiện xử lý với nội dung article_content ở đây
            entry = {
                'ID': id,
                'Link' : link,
                'Title' : title,
                'Content' : content
            }
            with lock:
                data.append(entry)
            with lock:
                with open("cookBeo.json", "w", encoding="utf-8") as json_file:
                    json.dump(data, json_file, ensure_ascii=False, indent=4)
            print(f"ID: {id}")
            print(f'link: {link}')
            # print("Content:", content)
            print("=" * 150)   
            count_id += 1
            
def recursion_next_page(link, retry_count=0):
    list_links = get_link_content_cook(link)
    if list_links:
        for link_content in list_links:
            get_content(link_content)

    soup = response(link)
    pagination = soup.find('ul',class_ = 'pagination')
    try:
        if pagination is not None:
            if pagination.find('li', class_='page-item disabled'):
                return
            else:
                next_page_link = pagination.find('li', class_='page-item active').find_next('li').a['href']
                print(f'====== Next link {next_page_link}\n')

                recursion_next_page(next_page_link)
        # else:
        #     print(f"No pagination found for link: {link}")
    except Exception as e:
        if retry_count < MAX_RETRIES:
            print(f'An error occurred: {e}. Retrying at {retry_count}/{MAX_RETRIES}...')
            time.sleep(2)
            recursion_next_page(link, retry_count +1)
        else:
            print(f"Max retries reached for link: {link}. Skipping...")


def main():
    global count_id
    category_links = get_links_from_page(main_url)
    threads = []

    for category_link in category_links:
        print(f'')
        recursion_next_page(category_link)

    #     thread = threading.Thread(target=recursion_next_page, args=(category_link,))
    #     threads.append(thread)
    #     thread.start()
    #     recursion_next_page(category_link)

    # for thread in threads:
    #     thread.join()

if __name__ == "__main__":
    main()
