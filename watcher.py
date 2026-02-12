import logging
from time import sleep

import requests
import telegram
from environs import Env

env = Env()
env.read_env()

logging.basicConfig(
    level=env.str('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(name)s] %(levelname)s %(message)s'
)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('telegram').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def main():
    tg_token = env.str('TG_TOKEN')
    chat_id = env.str('TG_CHAT_ID')
    bot = telegram.Bot(token=tg_token)

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

            if response_data['status'] == 'timeout':
                payload['timestamp'] = response_data['timestamp_to_request']
            else:
                for attempt in response_data['new_attempts']:
                    lesson_title = attempt['lesson_title']
                    verdict =attempt['is_negative']
                    lesson_url = attempt['lesson_url']

                    if verdict:
                        verdict_message='К сожалению, в работе нашлись ошибки.'
                    else:
                        verdict_message=(
                            'Преподавателю все понравилось,'
                            ' можно приступать к следующему уроку.'
                        )

                    bot.sendMessage(
                        text=(
                            f'У вас проверили работу "{lesson_title}".\n'
                            f'Ссылка: {lesson_url}\n'
                            f'{verdict_message}'
                        ),
                        chat_id=chat_id
                    )

                payload['timestamp'] = response_data['last_attempt_timestamp']

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            telegram.error.NetworkError
        ):
            logger.warning(
                'Ошибка соединения,'
                ' подожду немного и попробую переподключиться...'
            )
            sleep(5)
            continue

        except requests.exceptions.HTTPError:
            logger.exception(f'Ошибка HTTP.')
            break

        except telegram.error.Forbidden:
            logger.exception(
                f'Возможно бота заблокировали, заканчиваю работу.'
            )
            break

        except telegram.error.BadRequest:
            logger.exception(f'Ошибка.')
            break

        except telegram.error.TelegramError:
            logger.exception(
                f'Упс... Серьезная проблема с телеграмм.\n'
                f'Попробую еще раз через время..'
            )
            sleep(60)
            continue


if __name__ == '__main__':
    main()
