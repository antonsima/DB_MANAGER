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

        self.__url: str = 'https://api.hh.ru/vacancies'
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
            'per_page': 1  # Ограничиваем количество результатов
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data['items']:
                return data['items'][0]['id']
            return None
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None

    def get_companies_with_vacancies(self, companies: list[str]) -> dict:
        """
        Получение списка вакансий в виде словарей, где ключ - это компания,
        а значение - это список вакансий этой компании
        """

        companies_with_id = {}

        for company in companies:
            company_id = self.get_employer_id(company)

            companies_with_id[company] = company_id

        for company, company_id in companies_with_id.items():
            self.__params['employer_id'] = company_id
            self.__params['page'] = 0

            response = self._BaseHeadHunterAPI__get_response(self.__url, self.__headers, self.__params)

            if response.status_code == 200:
                try:
                    vacancies = response.json()['items']
                except KeyError:
                    continue

                self.__companies_with_vacancies[company] = [vacancies]
                self.__params['page'] += 1
            elif response.status_code == 403:
                time.sleep(5)

                response = self._BaseHeadHunterAPI__get_response(self.__url, self.__headers, self.__params)

                try:
                    vacancies = response.json()['items']
                except KeyError:
                    continue

                self.__companies_with_vacancies[company].append(vacancies)
                self.__params['page'] += 1
            else:
                continue

            while self.__params.get('page') != 20:
                response = self._BaseHeadHunterAPI__get_response(self.__url, self.__headers, self.__params)

                if response.status_code == 200:
                    try:
                        vacancies = response.json()['items']
                    except KeyError:
                        continue
                    self.__companies_with_vacancies[company].append(vacancies)
                    self.__params['page'] += 1
                elif response.status_code == 403:
                    time.sleep(5)

                    response = self._BaseHeadHunterAPI__get_response(self.__url, self.__headers, self.__params)

                    try:
                        vacancies = response.json()['items']
                    except KeyError:
                        continue

                    self.__companies_with_vacancies[company].append(vacancies)
                    self.__params['page'] += 1
                else:
                    break

        return self.__companies_with_vacancies

    @property
    def companies_with_vacancies(self) -> dict:
        """ Геттер для компаний с вакансиями """

        return self.__companies_with_vacancies
