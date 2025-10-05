"""
Модель пользователя (клиента ресторана).
Содержит базовую информацию о клиентах системы бронирования.
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Модель пользователя (клиента ресторана)."""
    
    id: Optional[int] = None
    name: str = ""
    phone: str = ""
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Инициализация после создания объекта."""
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def __str__(self) -> str:
        """Строковое представление пользователя."""
        return f"User(id={self.id}, name='{self.name}', phone='{self.phone}')"
    
    def is_valid(self) -> bool:
        """Проверяет валидность данных пользователя."""
        return (
            bool(self.name.strip()) and
            bool(self.phone.strip())
        )
    
    def to_dict(self) -> dict:
        """Преобразует объект в словарь."""
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """Создает объект User из словаря."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            created_at=created_at
        )
