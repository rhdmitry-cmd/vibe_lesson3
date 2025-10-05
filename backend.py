"""
Backend для системы бронирования столов в ресторане.
Реализует CRUD операции для всех моделей системы.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from postgres_driver import PostgreSQLDriver
from models import User, Table, Booking, BookingStatus


class BookingBackend:
    """Backend класс для работы с системой бронирования."""
    
    def __init__(self, driver: Optional[PostgreSQLDriver] = None):
        """
        Инициализация backend.
        
        Args:
            driver: Экземпляр PostgreSQL драйвера. Если не указан, создается новый.
        """
        self.driver = driver or PostgreSQLDriver()
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Настраивает логгер для backend."""
        logger = logging.getLogger('BookingBackend')
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
        """Подключается к базе данных."""
        try:
            return self.driver.connect()
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {e}")
            return False
    
    def disconnect(self):
        """Отключается от базы данных."""
        self.driver.disconnect()
    
    def is_connected(self) -> bool:
        """Проверяет подключение к базе данных."""
        return self.driver.is_connected()
    
    # ==================== USER CRUD OPERATIONS ====================
    
    def create_user(self, name: str, phone: str) -> Optional[User]:
        """
        Создает нового пользователя.
        
        Args:
            name: Имя пользователя
            phone: Телефон пользователя
            
        Returns:
            User: Созданный пользователь или None в случае ошибки
        """
        try:
            if not self.is_connected():
                self.logger.error("Нет подключения к базе данных")
                return None
            
            # Создаем объект пользователя
            user = User(name=name, phone=phone)
            
            # Валидация
            if not user.is_valid():
                self.logger.error("Неверные данные пользователя")
                return None
            
            # Проверяем уникальность телефона
            existing_user = self.get_user_by_phone(phone)
            if existing_user:
                self.logger.error(f"Пользователь с телефоном {phone} уже существует")
                return None
            
            # Добавляем в базу данных
            query = """
                INSERT INTO users (name, phone)
                VALUES (%s, %s)
                RETURNING id, created_at
            """
            
            result = self.driver.execute_query(query, (name, phone))
            
            if result:
                user_data = result[0]
                user.id = user_data['id']
                user.created_at = user_data['created_at']
                
                return user
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания пользователя: {e}")
            return None
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Получает пользователя по ID.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            User: Пользователь или None если не найден
        """
        try:
            if not self.is_connected():
                return None
            
            query = "SELECT * FROM users WHERE id = %s"
            result = self.driver.execute_query(query, (user_id,))
            
            if result:
                return User.from_dict(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя {user_id}: {e}")
            return None
    
    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        Получает пользователя по телефону.
        
        Args:
            phone: Телефон пользователя
            
        Returns:
            User: Пользователь или None если не найден
        """
        try:
            if not self.is_connected():
                return None
            
            query = "SELECT * FROM users WHERE phone = %s"
            result = self.driver.execute_query(query, (phone,))
            
            if result:
                return User.from_dict(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения пользователя по телефону {phone}: {e}")
            return None
    
    def get_all_users(self) -> List[User]:
        """
        Получает всех пользователей.
        
        Returns:
            List[User]: Список всех пользователей
        """
        try:
            if not self.is_connected():
                return []
            
            query = "SELECT * FROM users ORDER BY created_at DESC"
            result = self.driver.execute_query(query)
            
            return [User.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения всех пользователей: {e}")
            return []
    
    def update_user(self, user_id: int, name: Optional[str] = None, 
                   phone: Optional[str] = None) -> Optional[User]:
        """
        Обновляет данные пользователя.
        
        Args:
            user_id: ID пользователя
            name: Новое имя (опционально)
            phone: Новый телефон (опционально)
            
        Returns:
            User: Обновленный пользователь или None в случае ошибки
        """
        try:
            if not self.is_connected():
                return None
            
            # Получаем текущие данные пользователя
            current_user = self.get_user(user_id)
            if not current_user:
                self.logger.error(f"Пользователь {user_id} не найден")
                return None
            
            # Обновляем только переданные поля
            new_name = name if name is not None else current_user.name
            new_phone = phone if phone is not None else current_user.phone
            
            # Проверяем уникальность телефона если он изменился
            if phone and phone != current_user.phone:
                existing_user = self.get_user_by_phone(phone)
                if existing_user:
                    self.logger.error(f"Пользователь с телефоном {phone} уже существует")
                    return None
            
            # Обновляем в базе данных
            query = """
                UPDATE users 
                SET name = %s, phone = %s
                WHERE id = %s
                RETURNING *
            """
            
            result = self.driver.execute_query(query, (new_name, new_phone, user_id))
            
            if result:
                updated_user = User.from_dict(result[0])
                return updated_user
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления пользователя {user_id}: {e}")
            return None
    
    def delete_user(self, user_id: int) -> bool:
        """
        Удаляет пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            if not self.is_connected():
                return False
            
            # Проверяем существование пользователя
            if not self.get_user(user_id):
                self.logger.error(f"Пользователь {user_id} не найден")
                return False
            
            # Удаляем пользователя (каскадное удаление бронирований)
            query = "DELETE FROM users WHERE id = %s"
            affected = self.driver.execute_update(query, (user_id,))
            
            if affected > 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
            return False
    
    # ==================== TABLE CRUD OPERATIONS ====================
    
    def create_table(self, number: int, capacity: int, location: str, is_active: bool = True) -> Optional[Table]:
        """
        Создает новый стол.
        
        Args:
            number: Номер стола
            capacity: Вместимость стола
            location: Расположение стола
            is_active: Активен ли стол для бронирования
            
        Returns:
            Table: Созданный стол или None в случае ошибки
        """
        try:
            if not self.is_connected():
                self.logger.error("Нет подключения к базе данных")
                return None
            
            # Создаем объект стола
            table = Table(number=number, capacity=capacity, location=location, is_active=is_active)
            
            # Валидация
            if not table.is_valid():
                self.logger.error("Неверные данные стола")
                return None
            
            # Проверяем уникальность номера стола
            existing_table = self.get_table_by_number(number)
            if existing_table:
                self.logger.error(f"Стол с номером {number} уже существует")
                return None
            
            # Добавляем в базу данных
            query = """
                INSERT INTO tables (number, capacity, location, is_active)
                VALUES (%s, %s, %s, %s)
                RETURNING id, created_at
            """
            
            result = self.driver.execute_query(query, (number, capacity, location, is_active))
            
            if result:
                table_data = result[0]
                table.id = table_data['id']
                table.created_at = table_data['created_at']
                
                return table
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания стола: {e}")
            return None
    
    def get_table(self, table_id: int) -> Optional[Table]:
        """
        Получает стол по ID.
        
        Args:
            table_id: ID стола
            
        Returns:
            Table: Стол или None если не найден
        """
        try:
            if not self.is_connected():
                return None
            
            query = "SELECT * FROM tables WHERE id = %s"
            result = self.driver.execute_query(query, (table_id,))
            
            if result:
                return Table.from_dict(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения стола {table_id}: {e}")
            return None
    
    def get_table_by_number(self, number: int) -> Optional[Table]:
        """
        Получает стол по номеру.
        
        Args:
            number: Номер стола
            
        Returns:
            Table: Стол или None если не найден
        """
        try:
            if not self.is_connected():
                return None
            
            query = "SELECT * FROM tables WHERE number = %s"
            result = self.driver.execute_query(query, (number,))
            
            if result:
                return Table.from_dict(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения стола по номеру {number}: {e}")
            return None
    
    def get_all_tables(self) -> List[Table]:
        """
        Получает все столы.
        
        Returns:
            List[Table]: Список всех столов
        """
        try:
            if not self.is_connected():
                return []
            
            query = "SELECT * FROM tables ORDER BY number"
            result = self.driver.execute_query(query)
            
            return [Table.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения всех столов: {e}")
            return []
    
    def get_available_tables(self, capacity: int, location: Optional[str] = None) -> List[Table]:
        """
        Получает доступные столы по вместимости и расположению.
        
        Args:
            capacity: Минимальная вместимость стола
            location: Расположение (опционально)
            
        Returns:
            List[Table]: Список доступных столов
        """
        try:
            if not self.is_connected():
                return []
            
            if location:
                query = """
                    SELECT * FROM tables 
                    WHERE is_active = TRUE 
                    AND capacity >= %s 
                    AND location = %s
                    ORDER BY number
                """
                result = self.driver.execute_query(query, (capacity, location))
            else:
                query = """
                    SELECT * FROM tables 
                    WHERE is_active = TRUE 
                    AND capacity >= %s
                    ORDER BY number
                """
                result = self.driver.execute_query(query, (capacity,))
            
            return [Table.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения доступных столов: {e}")
            return []
    
    def update_table(self, table_id: int, number: Optional[int] = None,
                    capacity: Optional[int] = None, location: Optional[str] = None,
                    is_active: Optional[bool] = None) -> Optional[Table]:
        """
        Обновляет данные стола.
        
        Args:
            table_id: ID стола
            number: Новый номер стола (опционально)
            capacity: Новая вместимость (опционально)
            location: Новое расположение (опционально)
            is_active: Новый статус активности (опционально)
            
        Returns:
            Table: Обновленный стол или None в случае ошибки
        """
        try:
            if not self.is_connected():
                return None
            
            # Получаем текущие данные стола
            current_table = self.get_table(table_id)
            if not current_table:
                self.logger.error(f"Стол {table_id} не найден")
                return None
            
            # Обновляем только переданные поля
            new_number = number if number is not None else current_table.number
            new_capacity = capacity if capacity is not None else current_table.capacity
            new_location = location if location is not None else current_table.location
            new_is_active = is_active if is_active is not None else current_table.is_active
            
            # Проверяем уникальность номера если он изменился
            if number and number != current_table.number:
                existing_table = self.get_table_by_number(number)
                if existing_table:
                    self.logger.error(f"Стол с номером {number} уже существует")
                    return None
            
            # Обновляем в базе данных
            query = """
                UPDATE tables 
                SET number = %s, capacity = %s, location = %s, is_active = %s
                WHERE id = %s
                RETURNING *
            """
            
            result = self.driver.execute_query(query, (new_number, new_capacity, new_location, new_is_active, table_id))
            
            if result:
                updated_table = Table.from_dict(result[0])
                return updated_table
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления стола {table_id}: {e}")
            return None
    
    def delete_table(self, table_id: int) -> bool:
        """
        Удаляет стол.
        
        Args:
            table_id: ID стола
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            if not self.is_connected():
                return False
            
            # Проверяем существование стола
            if not self.get_table(table_id):
                self.logger.error(f"Стол {table_id} не найден")
                return False
            
            # Удаляем стол (каскадное удаление бронирований)
            query = "DELETE FROM tables WHERE id = %s"
            affected = self.driver.execute_update(query, (table_id,))
            
            if affected > 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления стола {table_id}: {e}")
            return False
    
    # ==================== BOOKING CRUD OPERATIONS ====================
    
    def create_booking(self, user_id: int, table_id: int, booking_date: date,
                      booking_time: time, guests_count: int, duration_hours: float = 2.0,
                      special_requests: str = "") -> Optional[Booking]:
        """
        Создает новое бронирование.
        
        Args:
            user_id: ID пользователя
            table_id: ID стола
            booking_date: Дата бронирования
            booking_time: Время бронирования
            guests_count: Количество гостей
            duration_hours: Продолжительность в часах
            special_requests: Особые пожелания
            
        Returns:
            Booking: Созданное бронирование или None в случае ошибки
        """
        try:
            if not self.is_connected():
                self.logger.error("Нет подключения к базе данных")
                return None
            
            # Проверяем существование пользователя и стола
            user = self.get_user(user_id)
            if not user:
                self.logger.error(f"Пользователь {user_id} не найден")
                return None
            
            table = self.get_table(table_id)
            if not table:
                self.logger.error(f"Стол {table_id} не найден")
                return None
            
            # Проверяем, может ли стол вместить гостей
            if not table.can_accommodate(guests_count):
                self.logger.error(f"Стол {table_id} не может вместить {guests_count} гостей")
                return None
            
            # Проверяем, активен ли стол
            if not table.is_active:
                self.logger.error(f"Стол {table_id} неактивен для бронирования")
                return None
            
            # Создаем объект бронирования
            booking = Booking(
                user_id=user_id,
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time,
                guests_count=guests_count,
                duration_hours=duration_hours,
                special_requests=special_requests,
                status=BookingStatus.PENDING
            )
            
            # Валидация
            if not booking.is_valid():
                self.logger.error("Неверные данные бронирования")
                return None
            
            # Проверяем конфликты с существующими бронированиями
            conflicting_bookings = self.get_conflicting_bookings(table_id, booking_date, booking_time, duration_hours)
            if conflicting_bookings:
                self.logger.error(f"Найдены конфликтующие бронирования для стола {table_id}")
                return None
            
            # Добавляем в базу данных
            query = """
                INSERT INTO bookings (user_id, table_id, booking_date, booking_time, 
                                    guests_count, duration_hours, special_requests, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at, updated_at
            """
            
            result = self.driver.execute_query(query, (
                user_id, table_id, booking_date, booking_time,
                guests_count, duration_hours, special_requests, BookingStatus.PENDING.value
            ))
            
            if result:
                booking_data = result[0]
                booking.id = booking_data['id']
                booking.created_at = booking_data['created_at']
                booking.updated_at = booking_data['updated_at']
                
                return booking
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка создания бронирования: {e}")
            return None
    
    def get_booking(self, booking_id: int) -> Optional[Booking]:
        """
        Получает бронирование по ID.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Booking: Бронирование или None если не найдено
        """
        try:
            if not self.is_connected():
                return None
            
            query = "SELECT * FROM bookings WHERE id = %s"
            result = self.driver.execute_query(query, (booking_id,))
            
            if result:
                return Booking.from_dict(result[0])
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка получения бронирования {booking_id}: {e}")
            return None
    
    def get_all_bookings(self) -> List[Booking]:
        """
        Получает все бронирования.
        
        Returns:
            List[Booking]: Список всех бронирований
        """
        try:
            if not self.is_connected():
                return []
            
            query = "SELECT * FROM bookings ORDER BY booking_date DESC, booking_time DESC"
            result = self.driver.execute_query(query)
            
            return [Booking.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения всех бронирований: {e}")
            return []
    
    def get_bookings_by_user(self, user_id: int) -> List[Booking]:
        """
        Получает бронирования пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[Booking]: Список бронирований пользователя
        """
        try:
            if not self.is_connected():
                return []
            
            query = """
                SELECT * FROM bookings 
                WHERE user_id = %s 
                ORDER BY booking_date DESC, booking_time DESC
            """
            result = self.driver.execute_query(query, (user_id,))
            
            return [Booking.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения бронирований пользователя {user_id}: {e}")
            return []
    
    def get_bookings_by_table(self, table_id: int) -> List[Booking]:
        """
        Получает бронирования стола.
        
        Args:
            table_id: ID стола
            
        Returns:
            List[Booking]: Список бронирований стола
        """
        try:
            if not self.is_connected():
                return []
            
            query = """
                SELECT * FROM bookings 
                WHERE table_id = %s 
                ORDER BY booking_date DESC, booking_time DESC
            """
            result = self.driver.execute_query(query, (table_id,))
            
            return [Booking.from_dict(row) for row in result]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения бронирований стола {table_id}: {e}")
            return []
    
    def get_conflicting_bookings(self, table_id: int, booking_date: date,
                               booking_time: time, duration_hours: float) -> List[Booking]:
        """
        Получает конфликтующие бронирования.
        
        Args:
            table_id: ID стола
            booking_date: Дата бронирования
            booking_time: Время бронирования
            duration_hours: Продолжительность в часах
            
        Returns:
            List[Booking]: Список конфликтующих бронирований
        """
        try:
            if not self.is_connected():
                return []
            
            # Создаем временное бронирование для проверки конфликтов
            temp_booking = Booking(
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_hours=duration_hours,
                status=BookingStatus.PENDING
            )
            
            # Получаем все активные бронирования для этого стола в эту дату
            query = """
                SELECT * FROM bookings 
                WHERE table_id = %s 
                AND booking_date = %s
                AND status IN ('pending', 'confirmed')
                ORDER BY booking_time
            """
            result = self.driver.execute_query(query, (table_id, booking_date))
            
            conflicting = []
            for row in result:
                existing_booking = Booking.from_dict(row)
                if temp_booking.is_conflicting_with(existing_booking):
                    conflicting.append(existing_booking)
            
            return conflicting
            
        except Exception as e:
            self.logger.error(f"Ошибка проверки конфликтов: {e}")
            return []
    
    def update_booking_status(self, booking_id: int, status: BookingStatus) -> Optional[Booking]:
        """
        Обновляет статус бронирования.
        
        Args:
            booking_id: ID бронирования
            status: Новый статус
            
        Returns:
            Booking: Обновленное бронирование или None в случае ошибки
        """
        try:
            if not self.is_connected():
                return None
            
            # Проверяем существование бронирования
            current_booking = self.get_booking(booking_id)
            if not current_booking:
                self.logger.error(f"Бронирование {booking_id} не найдено")
                return None
            
            # Проверяем, можно ли изменить статус
            if not current_booking.can_be_cancelled() and status == BookingStatus.CANCELLED:
                self.logger.error(f"Бронирование {booking_id} нельзя отменить")
                return None
            
            # Обновляем статус
            query = """
                UPDATE bookings 
                SET status = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING *
            """
            
            result = self.driver.execute_query(query, (status.value, booking_id))
            
            if result:
                updated_booking = Booking.from_dict(result[0])
                return updated_booking
            
            return None
            
        except Exception as e:
            self.logger.error(f"Ошибка обновления статуса бронирования {booking_id}: {e}")
            return None
    
    def delete_booking(self, booking_id: int) -> bool:
        """
        Удаляет бронирование.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            bool: True если удаление успешно
        """
        try:
            if not self.is_connected():
                return False
            
            # Проверяем существование бронирования
            if not self.get_booking(booking_id):
                self.logger.error(f"Бронирование {booking_id} не найдено")
                return False
            
            # Удаляем бронирование
            query = "DELETE FROM bookings WHERE id = %s"
            affected = self.driver.execute_update(query, (booking_id,))
            
            if affected > 0:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Ошибка удаления бронирования {booking_id}: {e}")
            return False
    
    # ==================== UTILITY METHODS ====================
    
    def get_booking_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по бронированиям.
        
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        try:
            if not self.is_connected():
                return {}
            
            # Общая статистика
            total_bookings = self.driver.execute_query("SELECT COUNT(*) as count FROM bookings")[0]['count']
            
            # Статистика по статусам
            status_stats = self.driver.execute_query("""
                SELECT status, COUNT(*) as count 
                FROM bookings 
                GROUP BY status
            """)
            
            # Статистика по столам
            table_stats = self.driver.execute_query("""
                SELECT t.number, t.location, COUNT(b.id) as bookings_count
                FROM tables t
                LEFT JOIN bookings b ON t.id = b.table_id
                GROUP BY t.id, t.number, t.location
                ORDER BY bookings_count DESC
            """)
            
            return {
                'total_bookings': total_bookings,
                'status_breakdown': {row['status']: row['count'] for row in status_stats},
                'table_popularity': [
                    {
                        'table_number': row['number'],
                        'location': row['location'],
                        'bookings_count': row['bookings_count']
                    }
                    for row in table_stats
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def __enter__(self):
        """Поддержка контекстного менеджера."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Поддержка контекстного менеджера."""
        self.disconnect()


# Пример использования
if __name__ == "__main__":
    # Создание backend и работа с ним
    with BookingBackend() as backend:
        print("🚀 Тестирование BookingBackend")
        
        # Создание пользователя
        user = backend.create_user("Иван Петров", "+7-900-123-45-67")
        print(f"✅ Создан пользователь: {user}")
        
        # Создание стола
        table = backend.create_table(1, 4, "Основной зал")
        print(f"✅ Создан стол: {table}")
        
        # Создание бронирования
        from datetime import date, time
        booking = backend.create_booking(
            user_id=user.id,
            table_id=table.id,
            booking_date=date.today(),
            booking_time=time(19, 0),
            guests_count=3
        )
        print(f"✅ Создано бронирование: {booking}")
        
        # Получение всех бронирований
        all_bookings = backend.get_all_bookings()
        print(f"📊 Всего бронирований: {len(all_bookings)}")
        
        # Получение статистики
        stats = backend.get_booking_statistics()
        print(f"📈 Статистика: {stats}")
