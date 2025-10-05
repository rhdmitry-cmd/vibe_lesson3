"""
Модель бронирования.
Связывает пользователей и столы для системы бронирования ресторана.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, date, time, timedelta
from enum import Enum

from .users import User
from .tables import Table


class BookingStatus(Enum):
    """Статусы бронирования."""
    PENDING = "pending"      # ожидает подтверждения
    CONFIRMED = "confirmed"  # подтверждено
    CANCELLED = "cancelled"  # отменено
    COMPLETED = "completed"  # завершено


@dataclass
class Booking:
    """Модель бронирования стола."""
    
    id: Optional[int] = None
    user_id: int = 0
    table_id: int = 0
    booking_date: Optional[date] = None
    booking_time: Optional[time] = None
    duration_hours: float = 2.0  # продолжительность в часах
    guests_count: int = 0
    status: BookingStatus = BookingStatus.PENDING
    special_requests: str = ""  # особые пожелания
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Связанные объекты (заполняются при необходимости)
    user: Optional[User] = None
    table: Optional[Table] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта."""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now
    
    def __str__(self) -> str:
        """Строковое представление бронирования."""
        return f"Booking(id={self.id}, user_id={self.user_id}, table_id={self.table_id}, date={self.booking_date}, time={self.booking_time})"
    
    def is_valid(self) -> bool:
        """Проверяет валидность данных бронирования."""
        return (
            self.user_id > 0 and
            self.table_id > 0 and
            self.booking_date is not None and
            self.booking_time is not None and
            self.duration_hours > 0 and
            self.guests_count > 0
        )
    
    def is_active(self) -> bool:
        """Проверяет, активно ли бронирование."""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    
    def can_be_cancelled(self) -> bool:
        """Проверяет, можно ли отменить бронирование."""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED]
    
    def get_end_time(self) -> Optional[datetime]:
        """Возвращает время окончания бронирования."""
        if self.booking_date and self.booking_time:
            start_datetime = datetime.combine(self.booking_date, self.booking_time)
            # Преобразуем duration_hours в float для совместимости с timedelta
            duration_float = float(self.duration_hours) if self.duration_hours else 2.0
            return start_datetime + timedelta(hours=duration_float)
        return None
    
    def is_conflicting_with(self, other: 'Booking') -> bool:
        """Проверяет, конфликтует ли данное бронирование с другим."""
        if self.table_id != other.table_id or not self.is_active() or not other.is_active():
            return False
        
        if self.booking_date != other.booking_date:
            return False
        
        self_start = datetime.combine(self.booking_date, self.booking_time)
        self_duration_float = float(self.duration_hours) if self.duration_hours else 2.0
        self_end = self_start + timedelta(hours=self_duration_float)
        other_start = datetime.combine(other.booking_date, other.booking_time)
        other_duration_float = float(other.duration_hours) if other.duration_hours else 2.0
        other_end = other_start + timedelta(hours=other_duration_float)
        
        # Проверяем пересечение временных интервалов
        return not (self_end <= other_start or other_end <= self_start)
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'table_id': self.table_id,
            'booking_date': self.booking_date.isoformat() if self.booking_date else None,
            'booking_time': self.booking_time.isoformat() if self.booking_time else None,
            'duration_hours': self.duration_hours,
            'guests_count': self.guests_count,
            'status': self.status.value,
            'special_requests': self.special_requests,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Booking':
        """Создает объект Booking из словаря."""
        booking_date = None
        if data.get('booking_date'):
            if isinstance(data['booking_date'], str):
                booking_date = date.fromisoformat(data['booking_date'])
            else:
                booking_date = data['booking_date']
        
        booking_time = None
        if data.get('booking_time'):
            if isinstance(data['booking_time'], str):
                booking_time = time.fromisoformat(data['booking_time'])
            else:
                booking_time = data['booking_time']
        
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        updated_at = None
        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                updated_at = datetime.fromisoformat(data['updated_at'])
            else:
                updated_at = data['updated_at']
        
        status = BookingStatus.PENDING
        if data.get('status'):
            try:
                status = BookingStatus(data['status'])
            except ValueError:
                status = BookingStatus.PENDING
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', 0),
            table_id=data.get('table_id', 0),
            booking_date=booking_date,
            booking_time=booking_time,
            duration_hours=data.get('duration_hours', 2.0),
            guests_count=data.get('guests_count', 0),
            status=status,
            special_requests=data.get('special_requests', ''),
            created_at=created_at,
            updated_at=updated_at
        )
