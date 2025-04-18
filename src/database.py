import os
from abc import ABC, abstractmethod
import psycopg2 as db
from dotenv import load_dotenv


class BaseDBManager(ABC):
    """ Абстрактный класс для DBManager """

    @abstractmethod
    def get_companies_and_vacancies_count(self):
        pass

    @abstractmethod
    def get_all_vacancies(self):
        pass

    @abstractmethod
    def get_avg_salary(self):
        pass

    @abstractmethod
    def get_vacancies_with_higher_salary(self):
        pass

    @abstractmethod
    def get_vacancies_with_keyword(self):
        pass


class DBManager(BaseDBManager):
    def __init__(self, companies_with_vacancies: dict) -> None:
        self.organisations = companies_with_vacancies
        load_dotenv()
        self.__host = os.getenv('HOST')
        self.__database = os.getenv('DATABASE')
        self.__user = os.getenv('USER')
        self.__password = os.getenv('PASSWORD')

    def create_organisations_table(self):
        create_table_query = '''
DROP TABLE IF EXISTS organizations;
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

        for organisation_name in self.organisations.keys():
            cur.execute('INSERT INTO organizations (company_name) VALUES (%s);', organisation_name)

        conn.commit()

        cur.close()
        conn.close()

    def create_vacancies_table(self):
        create_table_query = '''
DROP TABLE IF EXISTS vacancies;
CREATE TABLE vacancies
(
organization_id INT,
company_name VARCHAR(100) NOT NULL,
vacancy_title VARCHAR(100) NOT NULL,
salary_from VARCHAR(50),
vacancy_url VARCHAR(255) NOT NULL,

CONSTRAINT fk_vacancies_organisations FOREIGN KEY(organization_id) REFERENCES organisations(organization_id)
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

        for organisation_name, vacancies in self.organisations.items():
            for vacancy in vacancies:

                vacancy_title = vacancy['name']

                try:
                    salary_from = vacancy['salary']['from']
                except (KeyError, TypeError):
                    salary_from = 0

                vacancy_url = vacancy['alternate_url']

                cur.execute(
                    'INSERT INTO vacancies (organization_id, company_name, vacancy_title, salary_from, vacancy_url) VALUES (%s, %s, %s, %s, %s);',
                    (org_id, organisation_name, vacancy_title, salary_from, vacancy_url))

            org_id += 1


        conn.commit()

        cur.close()
        conn.close()

    def get_companies_and_vacancies_count(self):
        query = """
SELECT 
organisations.company_name,
COUNT(vacancies.organization_id) AS vacancies_count
FROM 
organizations
LEFT JOIN 
vacancies ON organisations.organization_id = vacancies.organization_id
GROUP BY 
organisations.organization_id, organisations.company_name
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

        cur.close()
        conn.close()

        return companies

    def get_all_vacancies(self):
        query = """
SELECT
organisations.company_name,
vacancies.vacancy_title,
vacancies.salary_from,
vacancies.vacancy_url
FROM 
vacancies
JOIN 
organizations ON vacancies.organisation_id = organizations.id
ORDER BY 
organizations.company_name, vacancies.vacancy_title;
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

        vacancies = []
        for row in results:
            vacancies.append({
                "company_name": row[0],
                "vacancy_title": row[1],
                "salary_from": row[2],
                "vacancy_url": row[3]
            })

        cur.close()
        conn.close()

        return vacancies

    def get_avg_salary(self):

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

        cur.close()
        conn.close()

        return round(float(result[0]), 2)

