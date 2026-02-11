from pprint import pprint

import requests
from environs import Env

env = Env()
env.read_env()


def main():
    auth_token = env.str("DEVMAN_API_TOKEN")

    url = 'https://dvmn.org/api/user_reviews/'
    headers = {'Authorization': f'Token {auth_token}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    pprint(response.json())


if __name__ == '__main__':
    main()
