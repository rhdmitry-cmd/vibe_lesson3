"""
CLI приложение для бронирования столов в ресторане.
Простой интерфейс командной строки для управления бронированиями.
"""

import sys
from datetime import date, time, datetime, timedelta
from typing import Optional, List
from backend import BookingBackend
from models import User, Table, Booking, BookingStatus


class BookingCLI:
    """CLI приложение для бронирования столов."""
    
    def __init__(self):
        """Инициализация CLI приложения."""
        self.backend = BookingBackend()
        self.current_user: Optional[User] = None
    
    def print_header(self, title: str):
        """Выводит заголовок приложения."""
        print("=" * 60)
        print(f"🍽️  {title}")
        print("=" * 60)
    
    def print_menu(self):
        """Выводит главное меню."""
        print("\n📋 ГЛАВНОЕ МЕНЮ:")
        print("1. 👀 Показать забронированные столы")
        print("2. 📅 Забронировать стол")
        print("3. 👤 Войти/Зарегистрироваться")
        print("4. 📊 Мои бронирования")
        print("5. 📈 Статистика")
        print("6. 🔍 Проверить доступность столика")
        print("0. 🚪 Выход")
        print("-" * 60)
    
    def get_user_choice(self, prompt: str, valid_choices: List[str] = None) -> str:
        """Получает выбор пользователя с валидацией."""
        while True:
            try:
                choice = input(f"\n{prompt}: ").strip()
                
                if valid_choices and choice not in valid_choices:
                    print(f"❌ Неверный выбор. Доступные варианты: {', '.join(valid_choices)}")
                    continue
                
                return choice
            except KeyboardInterrupt:
                print("\n\n👋 До свидания!")
                sys.exit(0)
            except Exception as e:
                print(f"❌ Ошибка ввода: {e}")
    
    def get_user_info(self) -> Optional[User]:
        """Получает информацию о пользователе для входа/регистрации."""
        print("\n👤 ВХОД / РЕГИСТРАЦИЯ")
        print("-" * 30)
        
        phone = self.get_user_choice("Введите телефон").strip()
        if not phone:
            print("❌ Телефон не может быть пустым")
            return None
        
        # Проверяем, существует ли пользователь
        existing_user = self.backend.get_user_by_phone(phone)
        
        if existing_user:
            print(f"✅ Пользователь найден: {existing_user.name}")
            return existing_user
        else:
            print("👤 Новый пользователь. Введите данные для регистрации:")
            
            name = self.get_user_choice("Имя").strip()
            if not name:
                print("❌ Имя не может быть пустым")
                return None
            
            # Создаем нового пользователя
            new_user = self.backend.create_user(name, phone)
            if new_user:
                print(f"✅ Пользователь зарегистрирован: {new_user.name}")
                return new_user
            else:
                print("❌ Ошибка регистрации пользователя")
                return None
    
    def show_booked_tables(self):
        """Показывает забронированные столы."""
        self.print_header("ЗАБРОНИРОВАННЫЕ СТОЛЫ")
        
        try:
            # Получаем все бронирования
            bookings = self.backend.get_all_bookings()
            
            if not bookings:
                print("✅ На данный момент нет забронированных столов")
                return
            
            # Группируем бронирования по датам
            bookings_by_date = {}
            for booking in bookings:
                booking_date = booking.booking_date
                if booking_date not in bookings_by_date:
                    bookings_by_date[booking_date] = []
                bookings_by_date[booking_date].append(booking)
            
            # Выводим забронированные столы по датам
            for booking_date in sorted(bookings_by_date.keys()):
                print(f"\n📅 {booking_date.strftime('%d.%m.%Y (%A)')}")
                print("-" * 50)
                
                day_bookings = bookings_by_date[booking_date]
                for booking in sorted(day_bookings, key=lambda b: b.booking_time):
                    # Получаем информацию о столе и пользователе
                    table = self.backend.get_table(booking.table_id)
                    user = self.backend.get_user(booking.user_id)
                    
                    status_emoji = {
                        BookingStatus.PENDING: "⏳",
                        BookingStatus.CONFIRMED: "✅",
                        BookingStatus.CANCELLED: "❌",
                        BookingStatus.COMPLETED: "🏁"
                    }
                    
                    status_text = {
                        BookingStatus.PENDING: "Ожидает",
                        BookingStatus.CONFIRMED: "Подтверждено",
                        BookingStatus.CANCELLED: "Отменено",
                        BookingStatus.COMPLETED: "Завершено"
                    }
                    
                    if table and user:
                        print(f"  🪑 Стол №{table.number} ({table.location})")
                        print(f"     ⏰ {booking.booking_time.strftime('%H:%M')} - {booking.get_end_time().strftime('%H:%M') if booking.get_end_time() else 'N/A'}")
                        print(f"     👥 {booking.guests_count} гостей")
                        print(f"     👤 {user.name} ({user.phone})")
                        print(f"     {status_emoji.get(booking.status, '❓')} {status_text.get(booking.status, 'Неизвестно')}")
                        if booking.special_requests:
                            print(f"     💬 {booking.special_requests}")
                        print()
            
            print(f"📊 Всего забронированных столов: {len(bookings)}")
            
        except Exception as e:
            print(f"❌ Ошибка получения данных: {e}")
    
    def check_table_availability(self, table_id: int, booking_date: date, 
                               booking_time: time, duration_hours: float) -> bool:
        """Проверяет доступность стола."""
        try:
            # Получаем стол
            table = self.backend.get_table(table_id)
            if not table:
                print(f"❌ Стол с ID {table_id} не найден")
                return False
            
            if not table.is_active:
                print(f"❌ Стол №{table.number} неактивен для бронирования")
                return False
            
            # Проверяем конфликты
            conflicting_bookings = self.backend.get_conflicting_bookings(
                table_id, booking_date, booking_time, duration_hours
            )
            
            if conflicting_bookings:
                print(f"❌ Стол №{table.number} занят в указанное время")
                print("📅 Конфликтующие бронирования:")
                for conflict in conflicting_bookings:
                    user = self.backend.get_user(conflict.user_id)
                    user_name = user.name if user else "Неизвестный"
                    print(f"   ⏰ {conflict.booking_time.strftime('%H:%M')} - {conflict.get_end_time().strftime('%H:%M') if conflict.get_end_time() else 'N/A'} ({user_name})")
                return False
            
            print(f"✅ Стол №{table.number} доступен!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка проверки доступности: {e}")
            return False
    
    def book_table_step1_check_availability(self) -> Optional[dict]:
        """Шаг 1: Проверка доступности стола."""
        print("\n📅 БРОНИРОВАНИЕ СТОЛА - ШАГ 1")
        print("-" * 40)
        print("🔍 Проверка доступности стола")
        
        try:
            # Получаем дату
            date_input = self.get_user_choice("Введите дату (YYYY-MM-DD) или нажмите Enter для сегодня")
            if not date_input:
                booking_date = date.today()
            else:
                booking_date = datetime.strptime(date_input, "%Y-%m-%d").date()
            
            print(f"📅 Выбранная дата: {booking_date.strftime('%d.%m.%Y (%A)')}")
            
            # Получаем время
            time_input = self.get_user_choice("Введите время (HH:MM)")
            try:
                booking_time = datetime.strptime(time_input, "%H:%M").time()
            except ValueError:
                print("❌ Неверный формат времени. Используйте HH:MM")
                return None
            
            print(f"⏰ Выбранное время: {booking_time.strftime('%H:%M')}")
            
            # Получаем продолжительность
            duration_input = self.get_user_choice("Продолжительность в часах (по умолчанию 2)", ["1", "1.5", "2", "2.5", "3", "3.5", "4"])
            duration_hours = float(duration_input) if duration_input else 2.0
            
            print(f"⏳ Продолжительность: {duration_hours} часов")
            
            # Получаем количество гостей
            guests_input = self.get_user_choice("Количество гостей")
            try:
                guests_count = int(guests_input)
                if guests_count <= 0:
                    print("❌ Количество гостей должно быть больше 0")
                    return None
            except ValueError:
                print("❌ Неверное количество гостей")
                return None
            
            print(f"👥 Количество гостей: {guests_count}")
            
            # Показываем доступные столы
            print(f"\n🔍 Поиск доступных столов...")
            available_tables = self.backend.get_available_tables(guests_count)
            
            if not available_tables:
                print(f"❌ Нет доступных столов для {guests_count} гостей")
                return None
            
            print(f"\n🪑 Доступные столы для {guests_count} гостей:")
            print("-" * 50)
            
            available_options = []
            for i, table in enumerate(available_tables, 1):
                print(f"{i}. Стол №{table.number} - {table.capacity} мест ({table.location})")
                available_options.append(str(i))
            
            # Выбор стола
            choice = self.get_user_choice("Выберите стол (номер)", available_options)
            selected_table = available_tables[int(choice) - 1]
            
            # Проверяем доступность выбранного стола
            if self.check_table_availability(selected_table.id, booking_date, booking_time, duration_hours):
                return {
                    'table_id': selected_table.id,
                    'table_number': selected_table.number,
                    'booking_date': booking_date,
                    'booking_time': booking_time,
                    'duration_hours': duration_hours,
                    'guests_count': guests_count
                }
            else:
                return None
                
        except Exception as e:
            print(f"❌ Ошибка на шаге 1: {e}")
            return None
    
    def book_table_step2_confirm_booking(self, booking_data: dict) -> bool:
        """Шаг 2: Подтверждение и создание бронирования."""
        print("\n📅 БРОНИРОВАНИЕ СТОЛА - ШАГ 2")
        print("-" * 40)
        print("✅ Подтверждение бронирования")
        
        try:
            # Проверяем, что пользователь авторизован
            if not self.current_user:
                print("❌ Необходимо войти в систему")
                user = self.get_user_info()
                if not user:
                    return False
                self.current_user = user
            
            # Показываем данные бронирования
            table = self.backend.get_table(booking_data['table_id'])
            print(f"\n📋 ДАННЫЕ БРОНИРОВАНИЯ:")
            print(f"👤 Пользователь: {self.current_user.name} ({self.current_user.phone})")
            print(f"🪑 Стол: №{table.number} ({table.location})")
            print(f"📅 Дата: {booking_data['booking_date'].strftime('%d.%m.%Y (%A)')}")
            print(f"⏰ Время: {booking_data['booking_time'].strftime('%H:%M')} - {(datetime.combine(booking_data['booking_date'], booking_data['booking_time']) + timedelta(hours=booking_data['duration_hours'])).strftime('%H:%M')}")
            print(f"👥 Гости: {booking_data['guests_count']} человек")
            print(f"⏳ Продолжительность: {booking_data['duration_hours']} часов")
            
            # Получаем особые пожелания
            special_requests = self.get_user_choice("Особые пожелания (необязательно, нажмите Enter для пропуска)")
            
            # Подтверждение
            confirm = self.get_user_choice("Подтвердить бронирование? (y/N)", ["y", "n", "Y", "N", "yes", "no", "да", "нет"])
            
            if confirm.lower() in ['y', 'yes', 'да']:
                # Создаем бронирование
                booking = self.backend.create_booking(
                    user_id=self.current_user.id,
                    table_id=booking_data['table_id'],
                    booking_date=booking_data['booking_date'],
                    booking_time=booking_data['booking_time'],
                    guests_count=booking_data['guests_count'],
                    duration_hours=booking_data['duration_hours'],
                    special_requests=special_requests
                )
                
                if booking:
                    print(f"\n🎉 БРОНИРОВАНИЕ СОЗДАНО УСПЕШНО!")
                    print(f"📋 Номер бронирования: {booking.id}")
                    print(f"📱 На телефон {self.current_user.phone} отправлено подтверждение")
                    return True
                else:
                    print("❌ Ошибка создания бронирования")
                    return False
            else:
                print("❌ Бронирование отменено")
                return False
                
        except Exception as e:
            print(f"❌ Ошибка на шаге 2: {e}")
            return False
    
    def book_table(self):
        """Полный процесс бронирования стола."""
        self.print_header("БРОНИРОВАНИЕ СТОЛА")
        
        # Шаг 1: Проверка доступности
        booking_data = self.book_table_step1_check_availability()
        if not booking_data:
            print("❌ Бронирование отменено на этапе проверки доступности")
            return
        
        # Шаг 2: Подтверждение и создание
        if self.book_table_step2_confirm_booking(booking_data):
            print("✅ Бронирование завершено успешно!")
        else:
            print("❌ Бронирование не завершено")
    
    def show_my_bookings(self):
        """Показывает бронирования текущего пользователя."""
        self.print_header("МОИ БРОНИРОВАНИЯ")
        
        if not self.current_user:
            print("❌ Необходимо войти в систему")
            user = self.get_user_info()
            if not user:
                return
            self.current_user = user
        
        try:
            bookings = self.backend.get_bookings_by_user(self.current_user.id)
            
            if not bookings:
                print("📭 У вас нет бронирований")
                return
            
            print(f"👤 Пользователь: {self.current_user.name} ({self.current_user.phone})")
            print(f"📊 Всего бронирований: {len(bookings)}")
            print("-" * 60)
            
            # Группируем по статусам
            status_groups = {}
            for booking in bookings:
                status = booking.status
                if status not in status_groups:
                    status_groups[status] = []
                status_groups[status].append(booking)
            
            status_names = {
                BookingStatus.PENDING: "⏳ Ожидают подтверждения",
                BookingStatus.CONFIRMED: "✅ Подтвержденные",
                BookingStatus.CANCELLED: "❌ Отмененные",
                BookingStatus.COMPLETED: "🏁 Завершенные"
            }
            
            for status, bookings_list in status_groups.items():
                print(f"\n{status_names.get(status, '❓ Неизвестные')} ({len(bookings_list)}):")
                print("-" * 40)
                
                for booking in sorted(bookings_list, key=lambda b: (b.booking_date, b.booking_time)):
                    table = self.backend.get_table(booking.table_id)
                    if table:
                        print(f"🪑 Стол №{table.number} ({table.location})")
                        print(f"   📅 {booking.booking_date.strftime('%d.%m.%Y')} в {booking.booking_time.strftime('%H:%M')}")
                        print(f"   👥 {booking.guests_count} гостей")
                        print(f"   ⏳ {booking.duration_hours} часов")
                        if booking.special_requests:
                            print(f"   💬 {booking.special_requests}")
                        print(f"   📋 ID бронирования: {booking.id}")
                        print()
            
        except Exception as e:
            print(f"❌ Ошибка получения бронирований: {e}")
    
    def show_statistics(self):
        """Показывает статистику по бронированиям."""
        self.print_header("СТАТИСТИКА БРОНИРОВАНИЙ")
        
        try:
            stats = self.backend.get_booking_statistics()
            
            if not stats:
                print("❌ Не удалось получить статистику")
                return
            
            print(f"📊 ОБЩАЯ СТАТИСТИКА:")
            print(f"📅 Всего бронирований: {stats.get('total_bookings', 0)}")
            
            print(f"\n📈 ПО СТАТУСАМ:")
            status_names = {
                'pending': '⏳ Ожидают подтверждения',
                'confirmed': '✅ Подтвержденные',
                'cancelled': '❌ Отмененные',
                'completed': '🏁 Завершенные'
            }
            
            for status, count in stats.get('status_breakdown', {}).items():
                status_name = status_names.get(status, f"❓ {status}")
                print(f"   {status_name}: {count}")
            
            print(f"\n🪑 ПОПУЛЯРНОСТЬ СТОЛОВ:")
            table_popularity = stats.get('table_popularity', [])
            if table_popularity:
                for table_info in sorted(table_popularity, key=lambda x: x['bookings_count'], reverse=True):
                    print(f"   🪑 Стол №{table_info['table_number']} ({table_info['location']}): {table_info['bookings_count']} бронирований")
            else:
                print("   📭 Нет данных о популярности столов")
            
        except Exception as e:
            print(f"❌ Ошибка получения статистики: {e}")
    
    def check_table_availability(self):
        """Проверяет доступность конкретного столика."""
        self.print_header("ПРОВЕРКА ДОСТУПНОСТИ СТОЛИКА")
        
        try:
            # Получаем дату
            date_input = self.get_user_choice("Введите дату (YYYY-MM-DD) или нажмите Enter для сегодня")
            if not date_input:
                booking_date = date.today()
            else:
                booking_date = datetime.strptime(date_input, "%Y-%m-%d").date()
            
            print(f"📅 Выбранная дата: {booking_date.strftime('%d.%m.%Y (%A)')}")
            
            # Получаем время
            time_input = self.get_user_choice("Введите время (HH:MM)")
            try:
                booking_time = datetime.strptime(time_input, "%H:%M").time()
            except ValueError:
                print("❌ Неверный формат времени. Используйте HH:MM")
                return
            
            print(f"⏰ Выбранное время: {booking_time.strftime('%H:%M')}")
            
            # Получаем продолжительность
            duration_input = self.get_user_choice("Продолжительность в часах (по умолчанию 2)", ["1", "1.5", "2", "2.5", "3", "3.5", "4"])
            duration_hours = float(duration_input) if duration_input else 2.0
            
            print(f"⏳ Продолжительность: {duration_hours} часов")
            
            # Получаем количество гостей
            guests_input = self.get_user_choice("Количество гостей")
            try:
                guests_count = int(guests_input)
                if guests_count <= 0:
                    print("❌ Количество гостей должно быть больше 0")
                    return
            except ValueError:
                print("❌ Неверное количество гостей")
                return
            
            print(f"👥 Количество гостей: {guests_count}")
            
            # Показываем все доступные столы
            print(f"\n🔍 Поиск доступных столов...")
            available_tables = self.backend.get_available_tables(guests_count)
            
            if not available_tables:
                print(f"❌ Нет доступных столов для {guests_count} гостей")
                return
            
            print(f"\n🪑 ДОСТУПНЫЕ СТОЛЫ ДЛЯ {guests_count} ГОСТЕЙ:")
            print("=" * 60)
            
            available_options = []
            free_tables = []
            
            for i, table in enumerate(available_tables, 1):
                # Проверяем доступность каждого стола
                is_available = self.check_table_availability_detailed(
                    table.id, booking_date, booking_time, duration_hours
                )
                
                status_emoji = "✅" if is_available else "❌"
                status_text = "Свободен" if is_available else "Занят"
                
                print(f"{i:2d}. {status_emoji} Стол №{table.number} - {table.capacity} мест ({table.location}) - {status_text}")
                
                if is_available:
                    free_tables.append((i, table))
                    available_options.append(str(i))
            
            if not free_tables:
                print(f"\n❌ Все столы заняты в указанное время!")
                print("💡 Попробуйте другое время или дату")
                return
            
            print(f"\n✅ Найдено {len(free_tables)} свободных столов из {len(available_tables)}")
            
            # Показываем детали для свободных столов
            print(f"\n📋 ДЕТАЛИ СВОБОДНЫХ СТОЛОВ:")
            print("-" * 60)
            
            for option_num, table in free_tables:
                print(f"🪑 Стол №{table.number} ({table.location})")
                print(f"   📏 Вместимость: {table.capacity} мест")
                print(f"   📅 Дата: {booking_date.strftime('%d.%m.%Y (%A)')}")
                print(f"   ⏰ Время: {booking_time.strftime('%H:%M')} - {(datetime.combine(booking_date, booking_time) + timedelta(hours=duration_hours)).strftime('%H:%M')}")
                print(f"   ⏳ Продолжительность: {duration_hours} часов")
                print(f"   👥 Ваши гости: {guests_count} человек")
                print()
            
            # Предложение забронировать
            response = self.get_user_choice("Хотите забронировать один из свободных столов? (y/N)", ["y", "n", "Y", "N", "yes", "no", "да", "нет"])
            
            if response.lower() in ['y', 'yes', 'да']:
                print("\n🔄 Переходим к бронированию...")
                self.book_table_from_availability_check(booking_date, booking_time, duration_hours, guests_count, free_tables)
            
        except Exception as e:
            print(f"❌ Ошибка проверки доступности: {e}")
    
    def check_table_availability_detailed(self, table_id: int, booking_date: date, 
                                        booking_time: time, duration_hours: float) -> bool:
        """Детальная проверка доступности конкретного стола."""
        try:
            # Получаем стол
            table = self.backend.get_table(table_id)
            if not table or not table.is_active:
                return False
            
            # Проверяем конфликты
            conflicting_bookings = self.backend.get_conflicting_bookings(
                table_id, booking_date, booking_time, duration_hours
            )
            
            return len(conflicting_bookings) == 0
            
        except Exception:
            return False
    
    def book_table_from_availability_check(self, booking_date: date, booking_time: time, 
                                         duration_hours: float, guests_count: int, free_tables: list):
        """Бронирует стол после проверки доступности."""
        try:
            print("\n📅 БРОНИРОВАНИЕ ВЫБРАННОГО СТОЛА")
            print("-" * 40)
            
            # Проверяем авторизацию
            if not self.current_user:
                print("❌ Необходимо войти в систему")
                user = self.get_user_info()
                if not user:
                    return
                self.current_user = user
            
            # Выбор стола
            available_options = [str(i) for i, _ in free_tables]
            choice = self.get_user_choice("Выберите стол (номер)", available_options)
            selected_option = int(choice)
            
            # Находим выбранный стол
            selected_table = None
            for option_num, table in free_tables:
                if option_num == selected_option:
                    selected_table = table
                    break
            
            if not selected_table:
                print("❌ Выбранный стол не найден")
                return
            
            # Показываем данные бронирования
            print(f"\n📋 ДАННЫЕ БРОНИРОВАНИЯ:")
            print(f"👤 Пользователь: {self.current_user.name} ({self.current_user.phone})")
            print(f"🪑 Стол: №{selected_table.number} ({selected_table.location})")
            print(f"📅 Дата: {booking_date.strftime('%d.%m.%Y (%A)')}")
            print(f"⏰ Время: {booking_time.strftime('%H:%M')} - {(datetime.combine(booking_date, booking_time) + timedelta(hours=duration_hours)).strftime('%H:%M')}")
            print(f"👥 Гости: {guests_count} человек")
            print(f"⏳ Продолжительность: {duration_hours} часов")
            
            # Получаем особые пожелания
            special_requests = self.get_user_choice("Особые пожелания (необязательно, нажмите Enter для пропуска)")
            
            # Подтверждение
            confirm = self.get_user_choice("Подтвердить бронирование? (y/N)", ["y", "n", "Y", "N", "yes", "no", "да", "нет"])
            
            if confirm.lower() in ['y', 'yes', 'да']:
                # Создаем бронирование
                booking = self.backend.create_booking(
                    user_id=self.current_user.id,
                    table_id=selected_table.id,
                    booking_date=booking_date,
                    booking_time=booking_time,
                    guests_count=guests_count,
                    duration_hours=duration_hours,
                    special_requests=special_requests
                )
                
                if booking:
                    print(f"\n🎉 БРОНИРОВАНИЕ СОЗДАНО УСПЕШНО!")
                    print(f"📋 Номер бронирования: {booking.id}")
                    print(f"📱 На телефон {self.current_user.phone} отправлено подтверждение")
                else:
                    print("❌ Ошибка создания бронирования")
            else:
                print("❌ Бронирование отменено")
                
        except Exception as e:
            print(f"❌ Ошибка бронирования: {e}")
    
    def run(self):
        """Запускает CLI приложение."""
        print("🚀 Запуск системы бронирования столов...")
        
        # Подключение к базе данных
        if not self.backend.connect():
            print("❌ Не удалось подключиться к базе данных")
            print("💡 Убедитесь, что:")
            print("   - PostgreSQL запущен")
            print("   - Настройки в .env файле корректны")
            print("   - Таблицы созданы (запустите install_database.py)")
            return
        
        print("✅ Подключение к базе данных установлено")
        
        try:
            while True:
                self.print_menu()
                
                choice = self.get_user_choice("Выберите действие", ["0", "1", "2", "3", "4", "5", "6"])
                
                if choice == "0":
                    print("\n👋 Спасибо за использование системы бронирования!")
                    break
                elif choice == "1":
                    self.show_booked_tables()
                elif choice == "2":
                    self.book_table()
                elif choice == "3":
                    user = self.get_user_info()
                    if user:
                        self.current_user = user
                        print(f"✅ Вы вошли как: {user.name}")
                elif choice == "4":
                    self.show_my_bookings()
                elif choice == "5":
                    self.show_statistics()
                elif choice == "6":
                    self.check_table_availability()
                
                # Пауза перед возвратом в меню
                if choice != "0":
                    input("\n⏸️  Нажмите Enter для продолжения...")
        
        except KeyboardInterrupt:
            print("\n\n👋 До свидания!")
        except Exception as e:
            print(f"\n❌ Критическая ошибка: {e}")
        finally:
            self.backend.disconnect()


def main():
    """Главная функция приложения."""
    try:
        app = BookingCLI()
        app.run()
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
