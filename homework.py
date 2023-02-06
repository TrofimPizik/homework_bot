import os
import logging
import exceptions
import time
import requests
from http import HTTPStatus

from dotenv import load_dotenv
import telegram


load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Функция для проверки обязательных переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for key, token in tokens.items():
        if not token:
            logging.critical(
                f'Отсутвует обязательная переменная окружения: {key}'
            )
            raise exceptions.RequiredTokenMissing(
                'Отсутсвует обязательная переменная окружения'
            )
    logging.debug('Переменные окружения успешно прошли проверку')


def send_message(bot, message):
    """Функция для оптравки сообщений в чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение отправлено')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(timestamp):
    """Функция для оптравки запроса к API."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
    if response.status_code != HTTPStatus.OK:
        logging.error(
            'Статус ответа не соответсвует ожидаемому: ожидаемый статус 200.'
        )
        raise exceptions.Incorrect_Http_Status('Некорректный стутс ответа')
    response = response.json()
    logging.debug('Запрос к API выполнен успешно')
    return response


def check_response(response):
    """Функция для проверки ответа от API на соответствие документации."""
    key = 'homeworks'
    if type(response) != dict:
        raise TypeError('Структура данных не является: dict')
    if key not in response:
        raise KeyError('Отсутсвует ключ: homeworks')
    if type(response['homeworks']) != list:
        raise TypeError('Структура данных не является: list')


def parse_status(homework):
    """Функция для получения статуса проверки работы."""
    keys = ['homework_name', 'status']
    for key in keys:
        if key not in homework.keys():
            raise KeyError(f'Отсутвует ключ: {keys[0]}')

    if not homework[keys[1]] in HOMEWORK_VERDICTS:
        raise exceptions.Documentation_Not_As_Expected(
            'Документация не соответсвует ожидаемой'
        )
    homework_status = homework['status']
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    error_massage = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homeworks = response['homeworks']
            if homeworks:
                homework = homeworks[0]
                message = parse_status(homework)
                send_message(bot, message)
            else:
                logging.debug('Статус работы не обновился')
        except Exception as error:
            message = logging.error(f'Сбой в работе программы: {error}')
            if error_massage != message:
                send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
