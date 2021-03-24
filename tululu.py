from requests.models import HTTPError
import urllib3
from urllib.parse import urljoin, urlsplit, unquote
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from os import path
from pathlib import Path
import argparse
from sys import stderr


def extract_img_link(soup, url):
    img_src = soup.find('div', class_='bookimage').find('img')['src']
    img_src = urljoin(url, img_src)
    return img_src


def check_for_redirect(response, n=1):
    """Проверка количества перенаправлений (редиректов) по URL.

    Args:
        response (requests): экземпляр request для проверки на редиректы.
        n (int): количество редиректов для проверки.

    Returns:
        boolean: было ли количество редиректов хотя бы n+1 раз.
    """
    return len(response.history) > n


def get_book_name(soup):
    """Получение названия и имени автора книги из объекта BeautifulSoup
       ("HTML-супа").

    Args:
        soup (BeautifulSoup): объект BeautifulSoup с HTML-кодом
                              страницы tululu.org.

    Returns:
        (str, str): кортеж из двух str: название и автор книги,
                    соответствено.
    """
    book_title, book_author = soup.find('div', id='content').find('h1').\
        get_text().split('::')
    book_title = book_title.strip()
    book_author = book_author.strip()
    return book_title, book_author


def write_txt_from_response(response, filename, folder='books/'):
    """Загрузка текстовых файлов книг.

    Ссылки на файлы извлекаются из объекта response.

    Args:
        response (requests): экземпляр request страницы с ссылкой на текст,
                             который нужно скачать.
        filename (str): Имя файла, с которым сохранять.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = f'{sanitize_filename(filename)}.txt'
    file_path = path.join(folder, filename)
    with open(f'{file_path}', 'w') as file:
        file.write(response.text)
    return file_path


def download_image(img_url, folder='images/'):
    """Загрузка картинок обложек книг.

    Args:
        img_url (str): Cсылка на картинку, которую нужно скачать.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = unquote(urlsplit(img_url).path.split('/')[-1])

    response_img = requests.get(img_url, verify=False)
    response_img.raise_for_status()
    with open(f'{path.join(folder, f"{filename}")}', 'wb') as file:
        file.write(response_img.content)
    return path.join(folder, f'{filename}')


def parse_book_page(soup):
    """Разбор (парсинг) информации о книге на сайте
       tululu.org.

       Функция получает название книги, имя
       автора книги, отзывы по книге, список жанров книги.

    Args:
        soup (BeautifulSoup): объект BeautifulSoup с HTML-кодом
                              страницы tululu.org.

    Returns:
        dict: Словарь с названием книги, именем автора книги,
              отзывами по книге, список жанров книги.
    """
    book_name, book_author = get_book_name(soup)
    feedbacks = soup.find_all('div', class_='texts')
    for i in range(len(feedbacks)):
        feedbacks[i] = feedbacks[i].find('span', class_='black')
    genres = soup.find('span', class_='d_book').find_all('a')
    genres_clean = [genre.find(text=True) for genre in genres]
    return {"Book name": book_name, "Book author": book_author,
            "Feedbacks": feedbacks, "Genres": genres_clean}


def cli_arguments():
    parser = argparse.ArgumentParser(
        description="""Программа показывает информацию о запрашиваемых книгах,
        скачивает их и их обложки."""
        )
    parser.add_argument('start_id', help='Начальный индекс книги',
                        default=1, nargs='?', type=int)
    parser.add_argument('end_id', help='Конечный индекс книги',
                        default=100, nargs='?', type=int)
    return parser.parse_args()


def display_book_info(book_id, book_info):
    print(f"Индекс {book_id}")
    print(f"Заголовок: {book_info['Book name']}")
    print(book_info['Genres'])
    for feedback in book_info['Feedbacks']:
        print(feedback.getText())
    print()


def main():
    args = cli_arguments()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    base_url = 'https://tululu.org/b'
    download_url = 'https://tululu.org/txt.php?id='

    print(f"Стартовый индекс книги: {args.start_id}")
    print(f"Конечный индекс книги: {args.end_id}")
    print()
    book_ids = []
    cover_responses = []

    
    for book_id in range(args.start_id, args.end_id+1):
        print(f"Обрабатываю индекс книги {book_id} для получения информации по книге...")
        print("\033[0J", "\033[3A", sep='\n', end='\n')
        cover_response = requests.get(f"{base_url}{book_id}",
                                  verify=False)
        
        if cover_response.ok:
            if not check_for_redirect(cover_response, 1):
                book_ids.append(book_id)
                cover_responses.append(cover_response)
            else:
                print("\033[2A", "\033[0J", sep='\n', end='\n')
                stderr.write(f"Книга с индексом {book_id} отсутствует. Ошибка 404.\n\n")
            print("\033[0J", "\033[2A", sep='\n', end='\n')
        else:
            stderr.write(f"Книга с индексом {book_id} не может быть скачана. Ошибка 302.\n\n")

    print("Загружаю книги...\n")

    for book_id, cover_response in zip(book_ids, cover_responses):
        download_response = requests.get(f"{download_url}{book_id}",
                                         verify=False)

        if not download_response.ok:
            print(f"""Не удалось скачать книгу (индекс {book_id}) из-за ошибки
                         HTTP.""")

        if check_for_redirect(download_response, 0):
            print(f"""Перенаправление ссылки по книге с индексом {book_id}. Отменяю скачивание книги.\n""")
            continue

        cover_soup = BeautifulSoup(cover_response.text, 'lxml')
        book_info = parse_book_page(cover_soup)
        display_book_info(book_id, book_info)
        write_txt_from_response(download_response,
                                f'{book_id}. {book_info["Book name"]}')
        img_url = extract_img_link(cover_soup, cover_response.url)
        download_image(img_url)


if __name__ == '__main__':
    main()
