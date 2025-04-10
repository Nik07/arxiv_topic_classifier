import os
import time

import logging
from datetime import datetime, date, timedelta
import arxiv
import json

from get_meta import get_paper_meta

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] #%(levelname)-8s %(filename)s:%(lineno)d - %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ArxivMetaParser:
    def __init__(
        self, 
        start_dt: datetime | date = None, 
        batch_size: int = 5000, 
        metadata_file: str = './arxiv_meta_parser/data/arxiv_paper_metadata_2020.jsonl',
        processed_file: str = './arxiv_meta_parser/data/processed_dates.txt'
    ):
        if start_dt:
            self.start_dt = start_dt
        else:
            try:
                self.start_dt = self.read_last_date_from_file()
            except Exception as e:
                self.start_dt = datetime(year=2019, month=1, day=1, hour=0, minute=0)
        self.batch_size = batch_size
        self.client = arxiv.Client()
        self.metadata_file = metadata_file
        self.processed_file = processed_file
        self.total_papers = 0
    
    def make_arxiv_query(self, input_dt: date | datetime = None):
        if input_dt is None:
            ymd = '20190101'
            start_time = '0000'
        else:
            if isinstance(input_dt, datetime):
                ymd = input_dt.strftime('%Y%m%d')
                start_time = input_dt.strftime('%H%M')
            elif isinstance(input_dt, date):
                ymd = input_dt.strftime('%Y%m%d')
                start_time = '0000'
            else:
                raise TypeError("Expected datetime.date or datetime.datetime")

        return f"submittedDate:[{ymd}{start_time} TO {ymd}2359]"
    
    def read_last_date_from_file(self, filepath: str = None) -> datetime:
        if filepath is None:
            filepath = self.processed_file
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]

        if not lines:
            raise ValueError("File is empty")

        last_date_str = lines[-1]
        try:
            return datetime.strptime(last_date_str, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Wrong date format: {last_date_str}. Expected YYYY-MM-DD.")
    
    def append_date_to_processed(self, dt: datetime | date, filepath: str = None):
        if filepath is None:
            filepath = self.processed_file
        if isinstance(dt, (datetime, date)):
            date_str = dt.strftime('%Y-%m-%d')
        else:
            raise TypeError("Expected datetime.date or datetime.datetime")

        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(f"{date_str}\n")
    
    def search(self, input_dt: date | datetime = None):
        if input_dt is None:
            input_dt = self.start_dt
        return arxiv.Search(
            query=self.make_arxiv_query(input_dt),
            max_results=self.batch_size,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Ascending
        )
    
    def add_meta_to_file(self, filepath: str, results: list[arxiv.Result]):
        with open(filepath, 'a', encoding='utf-8') as f:
            for i, result in enumerate(results, 1):
                json.dump(get_paper_meta(result), f)
                f.write('\n')
        print(f"\nЗагружено за текущий день {i} статей")
        self.total_papers += i

    def generate_date_range(self, start_date: date = None, end_date: date = None) -> list[date]:
        if start_date is None:
            start_date = self.start_dt
        if end_date is None:
            end_date = date.today()
        if start_date > end_date:
            raise ValueError("`start_date` must be earlier than or equal to `end_date`")

        delta = end_date - start_date
        return [start_date + timedelta(days=i) for i in range(delta.days + 1)]
    
    def start_parsing(self, start_dt: datetime | date = None, end_dt: datetime | date = None):
        self.start_time = time.time()
        if start_dt is None:
            start_dt = self.start_dt
        else:
            if isinstance(start_dt, datetime):
                ymd = start_dt.strftime('%Y%m%d')
                start_time = start_dt.strftime('%H%M')
            elif isinstance(start_dt, date):
                ymd = start_dt.strftime('%Y%m%d')
                start_time = '0000'
            else:
                raise TypeError("Expected datetime.date or datetime.datetime")
        
        days = self.generate_date_range(start_dt, end_dt)

        for i, day in enumerate(days, 1):
            try:
                print(f'Обработка даты: `{day.strftime('%Y-%m-%d')}`...')
                results = self.client.results(self.search(day))
                self.add_meta_to_file(self.metadata_file, results)
                self.append_date_to_processed(day)
                print(f'Всего статей загружено: {self.total_papers}')
                print(f'Общее время парсинга метадаты составляет: {time.time() - self.start_time:.2f} сек.')
            except Exception as e:
                logger.error('Обработка не удалась. %s', e)


if __name__ == '__main__':

    start_time = time.time()

    # print("Текущий рабочий каталог:", os.getcwd())

    parser_2024 = ArxivMetaParser(metadata_file='./arxiv_meta_parser/data/arxiv_paper_metadata_2024.jsonl')
    parser_2024.start_parsing(datetime(year=2024, month=9, day=15), datetime(year=2024, month=12, day=31))

    parser_2025 = ArxivMetaParser(metadata_file='./arxiv_meta_parser/data/arxiv_paper_metadata_2025.jsonl')
    parser_2025.start_parsing(datetime(year=2025, month=1, day=1), datetime(year=2025, month=4, day=6))

    print(f'Общее время парсинга: {time.time() - start_time:.2f} сек.')