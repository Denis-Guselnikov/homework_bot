import os
import sys
import requests
import logging
import time
import telegram
import exceptions
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s, %(funcName)s, %(lineno)s',
    filename='main.log',
)

PRACTICUM_TOKEN = os.getenv('prakticum_token')
TELEGRAM_TOKEN = os.getenv('telegram_tocen')
TELEGRAM_CHAT_ID = os.getenv('telegram_chat_id')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправка сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Message was successfully sent: {message}')
    except telegram.error.TelegramError as error:
        logging.error(f'Message has not been sent: {error}')


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    logging.info('Started an API request')
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Error during request for main API: {error}')

    if response.status_code != HTTPStatus.OK:
        message = f'Access error:{response.status_code}, {ENDPOINT}, {HEADERS}'
        logging.error(message)
        raise exceptions.ResponseException(message)

    try:
        return response.json()
    except Exception:
        logging.error('Server returned invalid json')
        send_message('Сервер вернул невалидный json')


def check_response(response):
    """Проверка ответа."""
    logging.info('Start checking the server response')
    if response['homeworks'] == []:
        message = ('There is no answer')
        logging.info(message)

    if isinstance(response, dict):
        homework = response.get('homeworks')
        curent_date = response.get('current_date')
        if curent_date is None:
            raise exceptions.ResponseException(
                f'Response has not {curent_date}')
        elif homework is None:
            raise exceptions.ResponseException(
                f'Response has not {homework}')
        elif not isinstance(homework, list):
            message = (f'Homework does not match the data type: {list}')
            raise TypeError(message)
        logging.info(f'Get result: {homework}')
        return homework


def parse_status(homework):
    """Получение homework_name и status."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    elif homework_status not in HOMEWORK_STATUSES:
        message = (
            f'Недокументированный статус домашней работы {homework_status}')
        logging.error(message)
        raise KeyError(message)


def check_tokens():
    """Проверка наличия ТОКЕНОВ."""
    tokens = all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    return tokens


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Missing or incorrect tokens!')
        sys.exit('Проблема с КОНСТАНТАМИ!')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            response_api = get_api_answer(current_timestamp)
            if response_api:
                homework = check_response(response_api)
                if homework:
                    status_message = parse_status(homework[0])
                    send_message(bot, status_message)
            else:
                logging.debug('Status of homework has not been updated.')
            current_timestamp = response_api.get('current_date')

        except Exception as error:
            message = f'Program malfunction: {error}'
            logging.error(message)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
