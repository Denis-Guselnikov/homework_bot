import os
import requests
import logging
import time
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    filename='main.log'    
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
    return bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Получение ответа от API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)                
    except Exception as error:
        logging.error(f'error during request for main API: {error}') 
    if response.status_code != 200:
        raise f'Error {response.status_code}'                       
    return response.json()     


def check_response(response):    
    """Проверка ответа."""
     
    try:        
        homework = response['homeworks']
    except Exception as error:
        message = (f'response does not meet expectations, error {error}')
        raise f'Error {message}'
    if not isinstance(response['homeworks'], list):
        message = (f'homeworks does not match the data type {list}')
        raise f'Error {message}'
    
    return homework


def parse_status(homework):
    """Получение homework_name и status"""
    homework_name = homework['homework_name']
    homework_status = homework['status']   
    verdict = ''

    if homework_status == 'rejected':
        verdict = 'Работа проверена: у ревьюера есть замечания.'
    elif homework_status == 'reviewing':
        verdict = 'Работа взята на проверку ревьюером.'
    elif homework_status == 'approved':
        verdict = 'Работа проверена: ревьюеру всё понравилось. Ура!'    
    else:       
        raise f'The work status is incorrect: {homework_status}'

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():      
    """Проверка наличия ТОКЕНОВ"""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True

def main():
    """Основная логика работы бота."""   

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    
    if check_tokens():    
        while True:
            try:
                response = get_api_answer(current_timestamp)
                homework = check_response(response)                
                current_timestamp = homework[0]['current_date']           
                time.sleep(RETRY_TIME)

            except Exception as error:
                logging.error(f'Error_main_exception while getting list of homeworks: {error}')
                message = f'Сбой в работе программы: {error}'
                print(message)
                time.sleep(RETRY_TIME)  

            else:
                message = parse_status(homework)
                send_message(bot, message)


if __name__ == '__main__':
    main()
