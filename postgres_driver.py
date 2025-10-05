"""
Драйвер для работы с PostgreSQL базой данных.
Предоставляет удобный интерфейс для подключения и выполнения запросов.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()


@dataclass
class DatabaseConfig:
    """Конфигурация подключения к базе данных."""
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8'


class PostgreSQLDriver:
    """Драйвер для работы с PostgreSQL базой данных."""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Инициализация драйвера.
        
        Args:
            config: Конфигурация подключения. Если не указана, 
                   загружается из переменных окружения.
        """
        self.config = config or self._load_config_from_env()
        self.connection: Optional[psycopg2.extensions.connection] = None
        self.logger = self._setup_logger()
    
    def _load_config_from_env(self) -> DatabaseConfig:
        """Загружает конфигурацию из переменных окружения."""
        return DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'test'),
            user=os.getenv('DB_USER', 'test_user'),
            password=os.getenv('DB_PASSWORD', ''),
        )
    
    def _setup_logger(self) -> logging.Logger:
        """Настраивает логгер для драйвера."""
        logger = logging.getLogger('PostgreSQLDriver')
        logger.setLevel(logging.WARNING)  # Отключаем INFO логи
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def connect(self) -> bool:
        """
        Устанавливает соединение с базой данных.
        
        Returns:
            bool: True если подключение успешно, False в противном случае.
        """
        try:
            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                cursor_factory=RealDictCursor
            )
            self.connection.autocommit = True
            self.logger.info(f"Успешное подключение к базе данных {self.config.database}")
            return True
            
        except psycopg2.Error as e:
            self.logger.error(f"Ошибка подключения к базе данных: {e}")
            return False
    
    def disconnect(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.connection:
            try:
                self.connection.close()
                self.logger.info("Соединение с базой данных закрыто")
            except psycopg2.Error as e:
                self.logger.error(f"Ошибка при закрытии соединения: {e}")
            finally:
                self.connection = None
    
    def is_connected(self) -> bool:
        """
        Проверяет, установлено ли соединение с базой данных.
        
        Returns:
            bool: True если соединение активно, False в противном случае.
        """
        if not self.connection:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except psycopg2.Error:
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает результат.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            List[Dict[str, Any]]: Результат запроса в виде списка словарей
            
        Raises:
            psycopg2.Error: При ошибке выполнения запроса
        """
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return [dict(row) for row in result]
                
        except psycopg2.Error as e:
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Выполняет INSERT, UPDATE или DELETE запрос.
        
        Args:
            query: SQL запрос
            params: Параметры для запроса
            
        Returns:
            int: Количество затронутых строк
            
        Raises:
            psycopg2.Error: При ошибке выполнения запроса
        """
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                self.connection.commit()
                return affected_rows
                
        except psycopg2.Error as e:
            self.connection.rollback()
            self.logger.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        Выполняет один запрос с множественными параметрами.
        
        Args:
            query: SQL запрос
            params_list: Список кортежей с параметрами
            
        Returns:
            int: Количество затронутых строк
            
        Raises:
            psycopg2.Error: При ошибке выполнения запроса
        """
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(query, params_list)
                affected_rows = cursor.rowcount
                self.connection.commit()
                return affected_rows
                
        except psycopg2.Error as e:
            self.connection.rollback()
            self.logger.error(f"Ошибка выполнения batch запроса: {e}")
            raise
    
    def begin_transaction(self) -> None:
        """Начинает транзакцию."""
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        self.connection.autocommit = False
    
    def commit_transaction(self) -> None:
        """Подтверждает транзакцию."""
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        self.connection.commit()
    
    def rollback_transaction(self) -> None:
        """Откатывает транзакцию."""
        if not self.is_connected():
            raise psycopg2.OperationalError("Нет соединения с базой данных")
        
        self.connection.rollback()
    
    @contextmanager
    def transaction(self):
        """
        Контекстный менеджер для работы с транзакциями.
        
        Example:
            with driver.transaction():
                driver.execute_update("INSERT INTO users ...")
                driver.execute_update("UPDATE users ...")
        """
        self.begin_transaction()
        try:
            yield
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise
    
    def __enter__(self):
        """Поддержка контекстного менеджера."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера."""
        self.disconnect()


# Пример использования
if __name__ == "__main__":
    # Создание и использование драйвера
    driver = PostgreSQLDriver()
    
    try:
        # Подключение к базе данных
        if driver.connect():
            print("Подключение к базе данных успешно!")
            
            # Пример выполнения SELECT запроса
            try:
                result = driver.execute_query("SELECT version()")
                print(f"Версия PostgreSQL: {result[0]['version']}")
            except psycopg2.Error as e:
                print(f"Ошибка выполнения запроса: {e}")
            
            # Пример использования транзакции
            try:
                with driver.transaction():
                    # Здесь можно выполнять несколько операций
                    # которые будут выполнены в одной транзакции
                    pass
            except Exception as e:
                print(f"Ошибка в транзакции: {e}")
        
    finally:
        driver.disconnect()
