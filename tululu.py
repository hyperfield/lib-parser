import urllib3
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from os import path
from pathlib import Path
import argparse


def extract_img_link(soup, response):
    response.raise_for_status()
    img_src = soup.find('div', class_='bookimage').find('img')['src']
    img_src = urljoin(response.url, img_src)
    return img_src


def check_for_redirect(response, n):
    """Функция проверяет сколько перенаправлений (редиректов) по URL было
       совершено.
    Args:
        response (requests): экземпляр request для проверки на редиректы.
        n (int): количество редиректов для проверки.

    Returns:
        boolean: было ли количество рекдиректов хотя бы n раз.
    """
    if len(response.history) > n:
        return True
    else:
        return False


def get_book_name(soup):
    """Функция получает название и имя автора книги из объекта BeautifulSoup
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


def download_txt(response, filename, folder='books/'):
    """Функция для скачивания текстовых файлов.
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

    response.raise_for_status()
    with open(f'{path.join(folder, filename)}', 'wb') as file:
        file.write(response.content)
        return path.join(folder, filename)


def download_image(img_url, folder='images/'):
    """Функция для скачивания картинок обложек книг.
    Args:
        img_url (str): Cсылка на картинку, которую нужно скачать.
        folder (str): Папка, куда сохранять.

    Returns:
        str: Путь до файла, куда сохранён текст.
    """
    Path(folder).mkdir(parents=True, exist_ok=True)
    filename = img_url.split("/")[-1]

    response_img = requests.get(img_url, verify=False)
    response_img.raise_for_status()
    with open(f'{path.join(folder, f"{filename}")}', 'wb') as file:
        file.write(response_img.content)
    return path.join(folder, f'{filename}')


def parse_book_page(soup):
    """Функция для разбора (парсинга) информации о книге на
       сайте tululu.org. Функция получает название книги, имя
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
    genres = soup.find('span', class_='d_book').find_all('a')
    genres_clean = [genre.find(text=True) for genre in genres]
    return {"Book name": book_name, "Book author": book_author,
            "Feedbacks": feedbacks, "Genres": genres_clean}


def main():
    description_1 = "Программа показывает информацию о запрашиваемых книгах,"
    description_2 = "скачивает их и их обложки."
    parser = argparse.ArgumentParser(
        description=f"{description_1} {description_2}"
        )
    parser.add_argument('start_id', help='Стартовый идентификатор книги')
    parser.add_argument('end_id', help='Крайний идентификатор книги')
    args = parser.parse_args()

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url_title = 'https://tululu.org/b'
    url_dl = 'https://tululu.org/txt.php?id='

    book_ids = [id for id in range(int(args.start_id), int(args.end_id)+1)
                if not check_for_redirect(
        requests.get(f"{url_title}{id}", verify=False), 1)]

    book_ids = [id for id in book_ids if not check_for_redirect(
        requests.get(f"{url_dl}{id}", verify=False), 0)]

    for id in book_ids:
        response_cover = requests.get(f"{url_title}{id}",
                                      verify=False)
        response_dl = requests.get(f"{url_dl}{id}",
                                   verify=False)
        soup = BeautifulSoup(response_cover.text, 'lxml')
        book_dict = parse_book_page(soup)
        img_url = extract_img_link(soup, response_cover)
        print(f"Заголовок: {book_dict['Book name']}")
        print(book_dict['Genres'])
        for feedback in book_dict['Feedbacks']:
            feedback = feedback.find('span', class_='black')
            print(feedback.getText())
        print()
        download_txt(response_dl,
                     f'{id}. {book_dict["Book name"]}')
        download_image(img_url)


if __name__ == '__main__':
    main()
