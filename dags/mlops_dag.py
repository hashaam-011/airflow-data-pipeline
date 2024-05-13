from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import csv
import re
import time
import os

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 5, 9),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'assignment2_dag',
    default_args=default_args,
    description='MLOps Assignment 2 DAG',
    schedule_interval=timedelta(days=1),
)

def extract_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    links = [link.get('href') for link in soup.find_all('a', href=True)]
    articles = soup.find_all('article')
    article_data = []
    for idx, article in enumerate(articles):
        title = article.find('h2').text.strip() if article.find('h2') else None
        description = article.find('p').text.strip() if article.find('p') else None
        article_data.append({'id': idx+1, 'title': title, 'description': description, 'source': url})

    return links, article_data

def save_to_csv(file_name, articles):
    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'title', 'description', 'source']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for article in articles:
            writer.writerow(article)

def preprocess(text):
    clean_text = re.sub('<.*?>', '', text)
    clean_text = re.sub('[^a-zA-Z]', ' ', clean_text)
    clean_text = clean_text.lower()
    clean_text = re.sub(' +', ' ', clean_text)
    return clean_text

def clean_data(data):
    cleaned_data = []
    for article in data:
        article['title'] = preprocess(article['title']) if article.get('title') else None
        article['description'] = preprocess(article['description']) if article.get('description') else None
        cleaned_data.append(article)
    return cleaned_data

def extract_data_task(url):
    print("Extracting data from:", url)
    links, articles = extract_data(url)
    return articles

def preprocess_data_task(articles):
    print("Preprocessing data")
    cleaned_data = clean_data(articles)
    return cleaned_data

def save_data_task(data):
    print("Saving data to CSV")
    filename = "/mnt/d/Study/Mlops/airflow-data-extraction-pipeline/data/extracted.csv"
    save_to_csv(filename, data)

extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract_data_task,
    op_kwargs={'url': 'https://www.dawn.com/'},
    dag=dag
)

preprocess_task = PythonOperator(
    task_id='preprocess_task',
    python_callable=preprocess_data_task,
    provide_context=True,
    dag=dag
)

save_task = PythonOperator(
    task_id='save_task',
    python_callable=save_data_task,
    provide_context=True,
    dag=dag
)

extract_task >> preprocess_task >> save_task
