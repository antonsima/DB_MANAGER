from abc import ABC, abstractmethod
from typing import Any
import time

import requests
from requests import Response


class BaseHeadHunterAPI(ABC):
    """ Абстрактный класс для HeadHunterAPI """

    @abstractmethod
    def get_companies_with_vacancies(self, keyword: str) -> list[dict]:
        pass

    @abstractmethod
    def __get_response(self, url: str, headers: dict, params: dict) -> 'Response':
        pass

    @abstractmethod
    def get_employer_id(self, company_name: str) -> str:
        pass


class HeadHunterAPI(BaseHeadHunterAPI):
    """
    Класс для работы с API HeadHunter
    Класс Parser является родительским классом, который вам необходимо реализовать
    """

    def __init__(self) -> None:

        self.__url_vacancies: str = 'https://api.hh.ru/vacancies'
        self.__url_employers: str = 'https://api.hh.ru/employers/'
        self.__headers: dict = {'User-Agent': 'HH-User-Agent'}
        self.__params: dict = {'employer_id': '', 'area': 113, 'page': 0, 'per_page': 100}
        self.__companies_with_vacancies: dict = {}

    def _BaseHeadHunterAPI__get_response(self, url: str, headers: dict, params: dict) -> Any:
        """
        Получение экземпляра класса Response
        """

        response = requests.get(url, headers=headers, params=params)

        return response

    def get_employer_id(self, company_name):
        """ Поиск ID работодателя по названию компании """

        url = 'https://api.hh.ru/employers'
        params = {
            'text': company_name,
            'only_with_vacancies': 'true',
            'per_page': 1
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['items']:
                print(data['items'][0]['id'])
                return data['items'][0]['id']
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None

    def get_companies_with_vacancies(self, companies_id: list[str]) -> dict:
        """
        Получение списка вакансий в виде словарей, где ключ - это компания,
        а значение - это список вакансий этой компании
        """

        for company_id in companies_id:

            self.__params['employer_id'] = company_id
            self.__params['page'] = 0
            response = self._BaseHeadHunterAPI__get_response(self.__url_vacancies, self.__headers, self.__params)

            company_name = self._BaseHeadHunterAPI__get_response(f'{self.__url_employers}{company_id}', {}, {}).json()['name']

            print(f'Попытка для {company_name} номер 0')

            if response.status_code == 200:
                try:
                    vacancies = response.json()['items']
                    # print(response.json())
                    # print(vacancies)
                except KeyError:
                    # print('KeyError')
                    # print(response.json())
                    continue

                if not vacancies:
                    continue
                self.__companies_with_vacancies[company_name] = vacancies
                self.__params['page'] += 1
            elif response.status_code == 403:
                # print('Ошибка 403')

                time.sleep(5)

                response = self._BaseHeadHunterAPI__get_response(self.__url_vacancies, self.__headers, self.__params)

                try:
                    vacancies = response.json()['items']
                    # print(vacancies)
                except KeyError:
                    # print('KeyError')
                    # print(response.json())
                    continue
                if not vacancies:
                    continue
                self.__companies_with_vacancies[company_name] = vacancies
                self.__params['page'] += 1
            else:
                # print('Неизвестный статус код')
                continue

            while self.__params.get('page') != 20:
                response = self._BaseHeadHunterAPI__get_response(self.__url_vacancies, self.__headers, self.__params)

                print(f'Попытка для {company_name} номер {self.__params.get('page')}')

                if response.status_code == 200:
                    try:
                        vacancies = response.json()['items']
                        # print(vacancies)
                    except KeyError:
                        # print('KeyError')
                        # print(response.json())
                        continue
                    if not vacancies:
                        break
                    self.__companies_with_vacancies[company_name].extend(vacancies)
                    self.__params['page'] += 1
                elif response.status_code == 403:
                    # print('Ошибка 403')
                    time.sleep(5)

                    response = self._BaseHeadHunterAPI__get_response(self.__url_vacancies, self.__headers, self.__params)

                    try:
                        vacancies = response.json()['items']
                        # print(vacancies)
                    except KeyError:
                        # print('KeyError')
                        # print(response.json())
                        continue
                    if not vacancies:
                        break
                    self.__companies_with_vacancies[company_name].extend(vacancies)
                    self.__params['page'] += 1
                else:
                    break
        # print(self.__companies_with_vacancies)
        return self.__companies_with_vacancies

    @property
    def companies_with_vacancies(self) -> dict:
        """ Геттер для компаний с вакансиями """

        return self.__companies_with_vacancies
