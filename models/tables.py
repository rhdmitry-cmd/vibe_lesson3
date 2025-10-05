"""
Модель стола ресторана.
Содержит информацию о столах в ресторане для системы бронирования.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Table:
    """Модель стола ресторана."""
    
    id: Optional[int] = None
    number: int = 0
    capacity: int = 0  # количество мест
    location: str = ""  # расположение (зал, терраса, VIP и т.д.)
    is_active: bool = True  # активен ли стол для бронирования
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __str__(self) -> str:
        """Строковое представление стола."""
        return f"Table(id={self.id}, number={self.number}, capacity={self.capacity}, location='{self.location}')"
    
    def is_valid(self) -> bool:
        """Проверяет валидность данных стола."""
        return (
            self.number > 0 and
            self.capacity > 0 and
            bool(self.location.strip())
        )
    
    def can_accommodate(self, guests_count: int) -> bool:
        """Проверяет, может ли стол вместить указанное количество гостей."""
        return self.is_active and guests_count <= self.capacity
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return {
            'id': self.id,
            'number': self.number,
            'capacity': self.capacity,
            'location': self.location,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Table':
        """Создает объект Table из словаря."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        return cls(
            id=data.get('id'),
            number=data.get('number', 0),
            capacity=data.get('capacity', 0),
            location=data.get('location', ''),
            is_active=data.get('is_active', True),
            created_at=created_at
        )
