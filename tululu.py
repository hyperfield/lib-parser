from requests.models import HTTPError
import urllib3
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from os import path
from pathlib import Path
import argparse
import random
from sys import stderr


def extract_img_link(soup, response):
    img_src = soup.find('div', class_='bookimage').find('img')['src']
    img_src = urljoin(response.url, img_src)
    return img_src


def check_for_redirect(response, n=0):
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


def download_txt_from_response(response, filename, folder='books/'):
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
    with open(f'{file_path}', 'wb') as file:
        file.write(response.content)
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
    filename = img_url.split("/")[-1]

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
    genres = soup.find('span', class_='d_book').find_all('a')
    genres_clean = [genre.find(text=True) for genre in genres]
    return {"Book name": book_name, "Book author": book_author,
            "Feedbacks": feedbacks, "Genres": genres_clean}


def main():
    parser = argparse.ArgumentParser(
        description="""Программа показывает информацию о запрашиваемых книгах,
        скачивает их и их обложки."""
        )
    rand_id_start = random.randint(1, 10001)
    rand_id_end = random.randint(rand_id_start, 10001)
    parser.add_argument('start_id', help='Начальный индекс книги',
                        default=rand_id_start, nargs='?', type=int)
    parser.add_argument('end_id', help='Конечный индекс книги',
                        default=rand_id_end, nargs='?', type=int)
    args = parser.parse_args()
    args.start_id = args.start_id
    args.end_id = args.end_id
    if args.start_id > args.end_id:
        args.end_id = random.randint(args.start_id, 10001)

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    base_url = 'https://tululu.org/b'
    dl_url = 'https://tululu.org/txt.php?id='

    print(f"Стартовый индекс книги: {args.start_id}")
    print(f"Конечный индекс книги: {args.end_id}")
    print()
    book_ids = []
    for book_id in range(args.start_id, args.end_id+1):
        print(f"Обрабатываю индекс книги {book_id} для получения информации по книге...")
        print("\033[0J")
        print("\033[3A")
        if not check_for_redirect(requests.get(f"{base_url}{book_id}",
                                  verify=False), 1):
            book_ids.append(book_id)
        else:
            print("\033[2A")
            print("\033[0J")
            stderr.write(f"Книга с индексом {book_id} отсутствует. Ошибка 404.\n\n")
    print("\033[0J")
    print("\033[2A")

    for book_id in book_ids:
        print(f"Обрабатываю индекс книги {book_id} для загрузки текста книги...")
        print("\033[0J")
        print("\033[3A")
        if check_for_redirect(requests.get(f"{dl_url}{book_id}",
                              verify=False)):
            book_ids.remove(book_id)
            print("\033[2A")
            print("\033[0J")
            stderr.write(f"Книга с индексом {book_id} не может быть скачана. Ошибка 302.\n\n")

    print("\033[2A")
    print("\033[0J")
    print("Загружаю книги...\n")
    for book_id in book_ids:
        response_cover = requests.get(f"{base_url}{book_id}",
                                      verify=False)
        try:
            response_cover.raise_for_status()
        except HTTPError:
            print(f"""Не удалось пропарсить книгу (индекс {book_id}) из-за ошибки
                      HTTP. Это не отменяет попытку скачивания книги.""")

        response_dl = requests.get(f"{dl_url}{book_id}",
                                   verify=False)

        if check_for_redirect(response_cover, 1):
            print(f"""Перенаправление ссылки по книге с индексом {book_id}. Отменяю
                      парсинг книги.""")

        try:
            response_dl.raise_for_status()
        except HTTPError:
            print(f"""Не удалось скачать книгу (индекс {book_id}) из-за ошибки
                         HTTP.""")

        if check_for_redirect(response_dl, 1):
            print(f"""Перенаправление ссылки по книге с индексом {book_id}. Отменяю
                      скачивание книги.""")

        soup = BeautifulSoup(response_cover.text, 'lxml')
        book_dict = parse_book_page(soup)
        img_url = extract_img_link(soup, response_cover)
        print(f"Индекс {book_id}")
        print(f"Заголовок: {book_dict['Book name']}")
        print(book_dict['Genres'])
        for feedback in book_dict['Feedbacks']:
            feedback = feedback.find('span', class_='black')
            print(feedback.getText())
        print()
        download_txt_from_response(response_dl,
                     f'{book_id}. {book_dict["Book name"]}')
        download_image(img_url)


if __name__ == '__main__':
    main()
