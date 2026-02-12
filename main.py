import logging
from time import sleep

import requests
from environs import Env

env = Env()
env.read_env()

logging.basicConfig(
    level=env.str('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s'
)
logging.getLogger("urllib3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    auth_token = env.str('DEVMAN_API_TOKEN')

    url = 'https://dvmn.org/api/long_polling/'
    headers = {'Authorization': f'Token {auth_token}'}
    payload = {}

    while True:
        try:
            response = requests.get(url, headers=headers, params=payload, timeout=100)
            response.raise_for_status()
            response_data = response.json()

            logger.debug(f'Ответ от сервера: {response_data}')

            if response_data['status'] == 'found':
                payload['timestamp'] = response_data['last_attempt_timestamp']
            else:
                payload['timestamp'] = response_data['timestamp_to_request']

        except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout
        ):
            logger.warning(
                'Ошибка соединения, подожду немного и попробую переподключиться...'
            )
            sleep(10)
            continue

        except requests.exceptions.HTTPError as error:
            logger.exception(f'Ошибка HTTP: {error}')
            break


if __name__ == '__main__':
    main()
