import logging
import os
import time
import requests

from dotenv import load_dotenv
import telegram

load_dotenv()

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

def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def parse_status(homework):
    homework_status = homework['status']
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'

def get_api_answer(timestamp):
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params = payload)
    except Exception as error:
        logging.error(f'Ошибка при запросе к API: {error}')
    response = response.json()
    return response     

def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 1664124651
    
    while True:
        response = get_api_answer(timestamp)
        homeworks = response['homeworks']
        if homeworks:
            homework = homeworks[0]
            message = parse_status(homework)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
