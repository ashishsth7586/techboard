# dependancy: mysql-connector-python (https://dev.mysql.com/downloads/connector/python/2.1.html)
import mysql.connector
import time

try:
    connection = mysql.connector.connect(user="scrapy", password="password",
        host = 'localhost', database='scrapyadmin')

    cursor = connection.cursor()

except mysql.connector.Error as err:
    print('Database connection failed')
    exit()

def get_job_timeframes():
    sql = ("SELECT start_time,end_time FROM job_timeframes")
    results = execute(sql)
    return results

def get_companies():
    sql = ("SELECT company FROM companies")
    results = execute(sql)
    return results

def get_keywords():
    sql = ("SELECT keyword FROM keywords")
    results = execute(sql)
    return results


   

def execute(tuple, single = False, args = {}, commit = False):
    cursor.execute(tuple, args)

    if commit == True:
        connection.commit()
    else:
        if single == True:
            return cursor.fetchone()
        else:
            return cursor.fetchall()

def lastrowid():
    return cursor.lastrowid

def close():
    connection.close()
