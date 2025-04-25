import os
from abc import ABC, abstractmethod

import psycopg2 as db
from dotenv import load_dotenv


class BaseDBManager(ABC):
    """ Абстрактный класс для DBManager """

    @abstractmethod
    def get_companies_and_vacancies_count(self) -> list[dict]:
        pass

    @abstractmethod
    def get_all_vacancies(self) -> list[dict]:
        pass

    @abstractmethod
    def get_avg_salary(self) -> float:
        pass

    @abstractmethod
    def get_vacancies_with_higher_salary(self) -> list[dict]:
        pass

    @abstractmethod
    def get_vacancies_with_keyword(self, keyword: str) -> list[dict]:
        pass


class DBManager(BaseDBManager):
    """ Класс для создания таблиц organizations и vacancies, и работы с ними"""

    def __init__(self, companies_with_vacancies: dict) -> None:
        self.organizations = companies_with_vacancies
        load_dotenv()
        self.__host = os.getenv('HOST')
        self.__database = os.getenv('DATABASE')
        self.__user = os.getenv('USER')
        self.__password = os.getenv('PASSWORD')

        self.create_organizations_table()
        self.create_vacancies_table()

    def create_organizations_table(self) -> None:
        """
        Создает таблицу organizations. Если такая существует, она удаляется
        """

        create_table_query = '''
DROP TABLE IF EXISTS organizations CASCADE;
CREATE TABLE organizations
(
organization_id SERIAL PRIMARY KEY,
company_name VARCHAR(255) NOT NULL
);
'''
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )
        cur = conn.cursor()
        cur.execute(create_table_query)

        for organization_name in self.organizations.keys():
            cur.execute('INSERT INTO organizations (company_name) VALUES (%s);', (organization_name, ))

        conn.commit()

        cur.close()
        conn.close()

    def create_vacancies_table(self) -> None:
        """
        Создает таблицу vacancies. Если такая существует, она удаляется
        """

        create_table_query = '''
DROP TABLE IF EXISTS vacancies;
CREATE TABLE vacancies
(
vacancy_id SERIAL PRIMARY KEY,
organization_id INT,
vacancy_title VARCHAR(100) NOT NULL,
salary_from NUMERIC,
vacancy_url VARCHAR(255) NOT NULL,

CONSTRAINT fk_vacancies_organizations FOREIGN KEY(organization_id) REFERENCES organizations(organization_id)
);
'''
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )
        cur = conn.cursor()
        cur.execute(create_table_query)

        org_id = 1

        for organization_name, vacancies in self.organizations.items():
            for vacancy in vacancies:

                vacancy_title = vacancy['name']

                try:
                    salary_from = vacancy['salary']['from']

                    if not salary_from:
                        salary_from = 0
                except (KeyError, TypeError):
                    salary_from = 0

                vacancy_url = vacancy['alternate_url']

                cur.execute(
                    'INSERT INTO vacancies (organization_id, vacancy_title, salary_from, vacancy_url) VALUES '
                    '(%s, %s, %s, %s);',
                    (org_id, vacancy_title, salary_from, vacancy_url))

            org_id += 1

        conn.commit()

        cur.close()
        conn.close()

    def get_companies_and_vacancies_count(self) -> list[dict]:
        """
        Возвращает список словарей с компаниями и количеством, предоставляемым ими вакансий
        company_name и vacancies_count
        """

        query = """
SELECT
organizations.company_name,
COUNT(vacancies.organization_id) AS vacancies_count
FROM
organizations
LEFT JOIN
vacancies ON organizations.organization_id = vacancies.organization_id
GROUP BY
organizations.organization_id, organizations.company_name
ORDER BY
vacancies_count DESC;
"""

        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )

        cur = conn.cursor()
        cur.execute(query)

        results = cur.fetchall()

        companies = []
        for row in results:
            companies.append({
                "company_name": row[0],
                "vacancies_count": row[1]
            })
            print(f'{row[0]}, Всего вакансий {row[1]}')

        cur.close()
        conn.close()

        return companies

    def get_all_vacancies(self) -> list[dict]:
        """
        Возвращает список словарей со всеми вакансиями
        company_name, vacancy_title, salary_from и vacancy_url
        """

        query = """
SELECT
organizations.company_name,
vacancies.vacancy_title,
vacancies.salary_from,
vacancies.vacancy_url
FROM
vacancies
JOIN
organizations ON vacancies.organization_id = organizations.organization_id
ORDER BY
salary_from;
"""
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )

        cur = conn.cursor()
        cur.execute(query)

        result = cur.fetchall()

        vacancies = []
        for row in result:
            vacancies.append({
                "company_name": row[0],
                "vacancy_title": row[1],
                "salary_from": int(row[2]),
                "vacancy_url": row[3]
            })

            print(f'{row[0]}, {row[1]}, Зарплата от {int(row[2])}, {row[3]}')

        cur.close()
        conn.close()

        return vacancies

    def get_avg_salary(self) -> float:
        """
        Возвращает среднюю зарплату по всем вакансиям
        """

        query = """
SELECT
AVG(salary_from) AS avg_from
FROM
vacancies
"""
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )

        cur = conn.cursor()
        cur.execute(query)

        result = cur.fetchone()
        if result is not None:
            print(f'Средняя зарплата по всем вакансиям = {round(float(result[0]), 2)} р.')

            cur.close()
            conn.close()

            return round(float(result[0]), 2)
        else:
            print('Средняя зарплата по всем вакансиям = 0 р.')

        cur.close()
        conn.close()

        return 0

    def get_vacancies_with_higher_salary(self) -> list[dict]:
        """
        Возвращает список словарей с вакансиями, у которых зарплата выше средней
        company_name, vacancy_title, salary_from и vacancy_url
        """

        avg_salary = self.get_avg_salary()

        query = f"""
SELECT
*
FROM vacancies
JOIN organizations USING(organization_id)
WHERE salary_from > {avg_salary}
ORDER BY salary_from
"""
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )

        cur = conn.cursor()
        cur.execute(query)

        result = cur.fetchall()

        vacancies = []

        for row in result:
            vacancies.append({
                "company_name": row[5],
                "vacancy_title": row[2],
                "salary_from": int(row[3]),
                "vacancy_url": row[4]
            })

            print(f'{row[5]}, {row[2]}, Зарплата от {int(row[3])}, {row[4]}')

        return vacancies

    def get_vacancies_with_keyword(self, keyword: str) -> list[dict]:
        """
        Возвращает список словарей с вакансиями, у которых в названии есть переданный keyword
        company_name, vacancy_title, salary_from и vacancy_url
        """

        query = """
SELECT *
FROM vacancies
JOIN organizations USING(organization_id)
WHERE vacancy_title ILIKE %s
ORDER BY salary_from
"""
        conn = db.connect(
            host=self.__host,
            database=self.__database,
            user=self.__user,
            password=self.__password
        )

        cur = conn.cursor()

        search_pattern = f"%{keyword}%"
        cur.execute(query, (search_pattern,))

        result = cur.fetchall()

        vacancies = []

        for row in result:
            vacancies.append({
                "company_name": row[5],
                "vacancy_title": row[2],
                "salary_from": int(row[3]),
                "vacancy_url": row[4]
            })
            print(f'{row[5]}, {row[2]}, Зарплата от {int(row[3])}, {row[4]}')

        return vacancies
