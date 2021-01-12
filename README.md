# Парсер книг с сайта tululu.org

Утилита для скачивания книг в текстовом формате с сайта [Tululu](http://tululu.org). Помимо скачивания книг программа также скачает картинки обложек скачивыемых книг, отобразит в терминале операционной системы название и автора(-ов) книг, а также сводку отзывов читателей о книгах.


## Как установить

Необходимо убедиться, что на вашем компьютере присутствует Python версии 3.x.
Теперь нужно инициализировать виртуальное окружение:

    python3 -m venv .lib-parser-venv

Теперь нужно активировать окружение:

    source .lib-parser-venv/bin/activate

После окончания работы деактивировать виртуальное окружение можно командой

    deactivate

После активации виртуального окружеия необходимо установить зависимости командой

    pip install -r requirements.txt

Всё это достаточно выполнить один раз. При этом активацию виртуального окружения (если оно еще не активировано) необходимо делать каждый раз перед началом использования утилиты.

## Аргументы

Данная утилита работает в текстовом режиме (в терминале) и принимает следующие аргументы командной строки:

    python3 tululu.py -h
показывает краткое описание утилиты и опции аргументов командной строки

    python3 tululu.py start_id end_id
где `start_id` и `end_id` это начальный и конечный идентификаторы, определяющие диапазон идентификаторов для скачивания книг.


### Цель проекта

Код написан в образовательных целях на онлайн-курсе для веб-разработчиков [dvmn.org](https://dvmn.org/).