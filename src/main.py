import os

import psycopg2 as db
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

from config import companies_id
from src.api import HeadHunterAPI
from src.database import DBManager

if __name__ == '__main__':

    load_dotenv()
    HOST = os.getenv('HOST')
    DATABASE = os.getenv('DATABASE')
    USER = os.getenv('USER')
    PASSWORD = os.getenv('PASSWORD')

    try:
        conn = db.connect(host=HOST,
                          user=USER,
                          password=PASSWORD)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()

        if DATABASE:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DATABASE,))
            exists = cursor.fetchone()

            if not exists:
                create_db_query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DATABASE))
                cursor.execute(create_db_query)

            cursor.close()
            conn.close()
        else:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", ('postgres',))
            exists = cursor.fetchone()

            if not exists:
                create_db_query = sql.SQL("CREATE DATABASE {}").format(sql.Identifier('postgres'))
                cursor.execute(create_db_query)

            cursor.close()
            conn.close()

    except db.Error as e:
        print("Ошибка при работе с PostgreSQL:", e)

    hh = HeadHunterAPI()
    companies_with_vacancies = hh.get_companies_with_vacancies(companies_id)

    db_manager = DBManager(companies_with_vacancies)

    while True:
        answer = input('''
Выберите действие:
1. Вывести список всех компаний и количество вакансий у каждой компании
2. Вывести список всех вакансий с указанием названия компании, названия вакансии, зарплаты и ссылки на вакансию
3. Вывести среднюю зарплату по вакансиям
4. Вывести список всех вакансий, у которых зарплата выше средней по всем вакансиям
5. Вывести список всех вакансий, в названии которых поисковое слово

Ответ: ''')

        if answer == '1':
            db_manager.get_companies_and_vacancies_count()
        elif answer == '2':
            db_manager.get_all_vacancies()
        elif answer == '3':
            db_manager.get_avg_salary()
        elif answer == '4':
            db_manager.get_vacancies_with_higher_salary()
        elif answer == '5':
            keyword = input('\nВведите слово для поиска: ')
            db_manager.get_vacancies_with_keyword(keyword)
