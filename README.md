# PostgreSQL Driver

Драйвер для работы с PostgreSQL базой данных на Python. Предоставляет удобный и безопасный интерфейс для подключения и выполнения запросов к PostgreSQL.

## Возможности

- ✅ Простое подключение к PostgreSQL
- ✅ Выполнение SELECT, INSERT, UPDATE, DELETE запросов
- ✅ Поддержка транзакций с автоматическим откатом
- ✅ Batch операции для массовых вставок
- ✅ Контекстные менеджеры для автоматического управления соединениями
- ✅ Обработка ошибок и логирование
- ✅ Загрузка конфигурации из переменных окружения
- ✅ Типизация с использованием type hints

## Установка

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Настройте переменные окружения в файле `.env`:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

## Быстрый старт

### Базовое использование

```python
from postgres_driver import PostgreSQLDriver

# Создание драйвера
driver = PostgreSQLDriver()

# Подключение к базе данных
if driver.connect():
    # Выполнение SELECT запроса
    result = driver.execute_query("SELECT * FROM users WHERE id = %s", (1,))
    print(result)
    
    # Выполнение UPDATE запроса
    affected_rows = driver.execute_update(
        "UPDATE users SET name = %s WHERE id = %s", 
        ("Новое имя", 1)
    )
    print(f"Обновлено строк: {affected_rows}")

# Закрытие соединения
driver.disconnect()
```

### Использование с контекстным менеджером

```python
from postgres_driver import PostgreSQLDriver

# Автоматическое управление соединением
with PostgreSQLDriver() as driver:
    if driver.is_connected():
        result = driver.execute_query("SELECT version()")
        print(f"Версия PostgreSQL: {result[0]['version']}")
```

### Работа с транзакциями

```python
from postgres_driver import PostgreSQLDriver

driver = PostgreSQLDriver()

try:
    driver.connect()
    
    # Использование контекстного менеджера для транзакций
    with driver.transaction():
        driver.execute_update("INSERT INTO users (name) VALUES (%s)", ("Иван",))
        driver.execute_update("INSERT INTO users (name) VALUES (%s)", ("Петр",))
        # Если произойдет ошибка, транзакция автоматически откатится
    
    # Ручное управление транзакциями
    driver.begin_transaction()
    try:
        driver.execute_update("UPDATE users SET status = %s", ("active",))
        driver.commit_transaction()
    except Exception:
        driver.rollback_transaction()
        raise

finally:
    driver.disconnect()
```

### Batch операции

```python
from postgres_driver import PostgreSQLDriver

driver = PostgreSQLDriver()

try:
    driver.connect()
    
    # Подготовка данных для массовой вставки
    users_data = [
        ("Иван", "ivan@example.com"),
        ("Петр", "petr@example.com"),
        ("Мария", "maria@example.com")
    ]
    
    # Выполнение batch операции
    affected_rows = driver.execute_many(
        "INSERT INTO users (name, email) VALUES (%s, %s)",
        users_data
    )
    print(f"Добавлено пользователей: {affected_rows}")

finally:
    driver.disconnect()
```

### Кастомная конфигурация

```python
from postgres_driver import PostgreSQLDriver, DatabaseConfig

# Создание кастомной конфигурации
config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="my_database",
    user="my_user",
    password="my_password"
)

driver = PostgreSQLDriver(config)
```

## API Reference

### Класс PostgreSQLDriver

#### Методы подключения

- `connect() -> bool` - Подключение к базе данных
- `disconnect() -> None` - Закрытие соединения
- `is_connected() -> bool` - Проверка состояния соединения

#### Методы выполнения запросов

- `execute_query(query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]` - Выполнение SELECT запросов
- `execute_update(query: str, params: Optional[tuple] = None) -> int` - Выполнение INSERT/UPDATE/DELETE запросов
- `execute_many(query: str, params_list: List[tuple]) -> int` - Batch операции

#### Методы управления транзакциями

- `begin_transaction() -> None` - Начало транзакции
- `commit_transaction() -> None` - Подтверждение транзакции
- `rollback_transaction() -> None` - Откат транзакции
- `transaction()` - Контекстный менеджер для транзакций

#### Контекстные менеджеры

- `with PostgreSQLDriver() as driver:` - Автоматическое управление соединением
- `with driver.transaction():` - Автоматическое управление транзакциями

### Класс DatabaseConfig

```python
@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8'
```

## Обработка ошибок

Драйвер использует стандартные исключения psycopg2:

- `psycopg2.OperationalError` - Ошибки подключения
- `psycopg2.ProgrammingError` - Ошибки в SQL запросах
- `psycopg2.IntegrityError` - Нарушения целостности данных
- `psycopg2.DatabaseError` - Общие ошибки базы данных

## Логирование

Драйвер автоматически логирует:
- Подключения и отключения
- Выполнение запросов
- Ошибки
- Транзакции

Уровень логирования можно настроить через стандартный модуль `logging`.

## Примеры

Смотрите файл `example_usage.py` для подробных примеров использования всех возможностей драйвера.

## Требования

- Python 3.7+
- psycopg2-binary 2.9.9+
- PostgreSQL 9.6+

## Лицензия

MIT License
