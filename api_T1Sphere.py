import requests
import base64
from datetime import datetime, timezone
from gigachat import GigaChat
import ssl
import urllib3
# Отключаем предупреждения о SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка SSL контекста для игнорирования ошибок сертификатов
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Инициализация GigaChat с отключенной проверкой SSL
giga = GigaChat(
    credentials="OWRlNjRhNDMtZGQ3OC00NmQyLWI2NTAtOWEyYTU0Mzk0MGQ1OjkwYmIwMDMzLWUyNTUtNGIwMS1iMjY5LThjZjcyZWQwNTZiNA==",
    verify_ssl_certs=False,  # Отключаем проверку SSL сертификатов
    ssl_context=ssl_context,
    model="GigaChat-Max"
)


def get_all_commits_with_pagination(project_name: str, repo_name: str, headers: dict, author: str = None,
                                    start_date: str = None, end_date: str = None):
    """Получить ВСЕ коммиты репозитория с пагинацией и фильтрацией"""
    base_url = "https://gateway-codemetrics.saas.sferaplatform.ru/app/sourcecode/api/api/v2"

    all_commits = []
    page = 1
    page_size = 100  # Максимальное количество коммитов на странице

    print(f"   📥 Получаем все коммиты репозитория {repo_name}...")

    # Преобразуем даты если они есть
    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None

    while True:
        try:
            # Параметры запроса
            params = {'page': page, 'limit': page_size}
            if author:
                params['author'] = author

            response = requests.get(
                f"{base_url}/projects/{project_name}/repos/{repo_name}/commits",
                headers=headers,
                params=params,
                verify=False
            )

            if response.status_code == 200:
                commits_data = response.json()
                commits = commits_data.get('data', [])

                if not commits:
                    break  # Больше нет коммитов

                # Фильтруем коммиты по дате если указаны даты
                if start_dt or end_dt:
                    filtered_commits = []
                    for commit in commits:
                        commit_date_str = commit.get('created_at', '')
                        if commit_date_str:
                            commit_dt = parse_iso_date(commit_date_str)
                            if commit_dt:
                                commit_dt_naive = commit_dt.replace(tzinfo=None)
                                start_dt_naive = start_dt.replace(tzinfo=None) if start_dt else None
                                end_dt_naive = end_dt.replace(tzinfo=None) if end_dt else None

                                # Проверяем попадает ли коммит в диапазон дат
                                date_match = True
                                if start_dt_naive and commit_dt_naive < start_dt_naive:
                                    date_match = False
                                if end_dt_naive and commit_dt_naive > end_dt_naive:
                                    date_match = False

                                if date_match:
                                    filtered_commits.append(commit)

                    all_commits.extend(filtered_commits)
                    print(
                        f"      Страница {page}: получено {len(commits)} коммитов, после фильтрации по дате: {len(filtered_commits)}")
                else:
                    all_commits.extend(commits)
                    print(f"      Страница {page}: получено {len(commits)} коммитов")

                # Проверяем, есть ли следующая страница
                if len(commits) < page_size:
                    break  # Это последняя страница

                # Если есть фильтр по дате и мы получили коммиты старше start_date, прерываем
                if start_dt and commits:
                    oldest_commit_date = None
                    for commit in commits:
                        commit_date_str = commit.get('created_at', '')
                        if commit_date_str:
                            commit_dt = parse_iso_date(commit_date_str)
                            if commit_dt:
                                if oldest_commit_date is None or commit_dt < oldest_commit_date:
                                    oldest_commit_date = commit_dt

                    if oldest_commit_date and oldest_commit_date.replace(tzinfo=None) < start_dt.replace(tzinfo=None):
                        print(f"      Достигнуты коммиты старше начальной даты, останавливаем пагинацию")
                        break

                page += 1

            else:
                print(f"   ❌ Ошибка получения коммитов (страница {page}): {response.status_code}")
                break

        except Exception as e:
            print(f"   ❌ Ошибка при получении страницы {page}: {e}")
            break

    print(f"   ✅ Всего получено коммитов: {len(all_commits)}")
    return all_commits


def get_commits_by_date_range(project_name: str, repo_name: str, start_date: str, username_, end_date: str,
                              headers: dict, show_diff: bool = False):
    """Получить коммиты за определенный период времени"""
    try:
        # Получаем ВСЕ коммиты с пагинацией и фильтрацией по дате
        all_commits = get_all_commits_with_pagination(
            project_name,
            repo_name,
            headers,
            author=username_,
            start_date=start_date,
            end_date=end_date
        )

        print(f"📅 Коммиты за период с {start_date} по {end_date}:")
        print(f"   Найдено коммитов: {len(all_commits)}")

        if all_commits:
            # Обрабатываем найденные коммиты
            process_commits_with_diff(project_name, repo_name, username_, headers, all_commits, show_diff)
        else:
            print("   ❌ Коммиты не найдены за указанный период")

        return all_commits

    except Exception as e:
        print(f"   Ошибка: {e}")
        return []


def process_commits_with_diff(project_name: str, repo_name: str, author: str, headers: dict, commits: list,
                              show_diff: bool = False):
    """Обработать коммиты с получением diff"""
    if not commits:
        return

    print(f"   Обрабатываем коммиты автора {author}:")

    # Фильтруем коммиты по автору (на всякий случай)
    author_commits = [commit for commit in commits if commit.get('author', {}).get('email') == author]

    if not author_commits:
        print(f"   ❌ У автора {author} нет коммитов в этом репозитории за указанный период")
        return

    print(f"   📊 Найдено коммитов автора: {len(author_commits)}")

    for i, commit in enumerate(author_commits):
        # Получаем сообщение коммита
        message = commit.get('message', 'No message')
        message_first_line = message.split('\n')[0]  # Первая строка сообщения

        # Получаем автора
        author_info = commit.get('author', {})
        author_name = author_info.get('name', 'Unknown') if isinstance(author_info, dict) else 'Unknown'

        # Получаем дату
        created_at = commit.get('created_at', 'Unknown')

        print(f"   {i + 1}. {author_name} ({created_at}): {message_first_line}")

        if show_diff:
            commit_hash = commit.get('hash', 'Unknown')
            if commit_hash in get_existing_commit_hashes():
                print(f"   ⏩ Коммит {commit_hash[:8]} уже оценен, пропускаем...")
                existing_evaluation = get_commit_evaluation_from_file(commit_hash)
                if existing_evaluation:
                    print(f"   📊 Существующая оценка:")
                    for line in existing_evaluation:
                        print(f"      {line}")
            else:
                # Получаем diff коммита
                diff_content = get_commit_diff_decoded(project_name, repo_name, commit_hash, headers)
                if diff_content:
                    # Получаем оценку от GigaChat
                    evaluation = get_commit_evaluation_with_gigachat(commit_hash, diff_content)
                    if evaluation:
                        save_commit_evaluation(commit_hash, evaluation)

        print()  # Пустая строка между коммитами


def parse_date(date_str: str):
    """Парсит дату в формате DD.MM.YYYY и добавляет UTC timezone"""
    try:
        dt = datetime.strptime(date_str, '%d.%m.%Y')
        # Делаем дату aware с UTC timezone
        return dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def parse_iso_date(iso_date_str: str):
    """Парсит ISO дату из API"""
    try:
        # Убираем Z и преобразуем в datetime
        clean_date = iso_date_str.replace('Z', '+00:00')
        return datetime.fromisoformat(clean_date)
    except ValueError:
        return None


def get_date_input():
    """Получить даты от пользователя"""
    print("\n📅 Введите диапазон дат для фильтрации коммитов")
    print("   Формат: DD.MM.YYYY (например: 01.01.2020)")

    while True:
        start_date = input("   Начальная дата: ").strip()
        if not start_date:
            print("   ❌ Дата не может быть пустой")
            continue

        start_dt = parse_date(start_date)
        if not start_dt:
            print("   ❌ Неверный формат даты. Используйте DD.MM.YYYY")
            continue
        break

    while True:
        end_date = input("   Конечная дата: ").strip()
        if not end_date:
            print("   ❌ Дата не может быть пустой")
            continue

        end_dt = parse_date(end_date)
        if not end_dt:
            print("   ❌ Неверный формат даты. Используйте DD.MM.YYYY")
            continue

        if end_dt < start_dt:
            print("   ❌ Конечная дата не может быть раньше начальной")
            continue
        break

    return start_date, end_date


def get_commit_evaluation_with_gigachat(commit_hash: str, diff_content: str):
    """Получить оценку коммита с помощью GigaChat"""
    try:
        # Ограничиваем размер diff для избежания переполнения контекста
        if len(diff_content) > 4000:
            diff_content = diff_content[:4000] + "... [содержимое обрезано]"

        prompt = f"""Ты строгий тимлид, который точен в оценках. Не усредняй баллы и следуй критериям буквально. Оцени следующий коммит СТРОГО по указанным критериям:

ПРАВИЛА ОЦЕНКИ:
1. РАЗМЕР - подсчитай общее количество добавленных и удаленных строк в коммите:
   1 балл - менее 10 строк изменений
   2 балла - 10-20 строк изменений
   3 балла - 20-50 строк изменений  
   4 балла - 50-80 строк изменений
   5 баллов - более 80 строк изменений

2. КАЧЕСТВО - проанализируй содержание изменений:
   1-2 балла - изменения явно вносят новые баги или ухудшают код
   3 балла - изменения нейтральны, но могли быть реализованы лучше
   4-5 баллов - изменения улучшают код, багов не вносят

3. СЛОЖНОСТЬ - оцени сложность реализации:
    1 балл - тривиальные изменения (опечатки, переименования)
    2 балла - простые изменения (корректировка формата, мелкие правки)
    3 балла - изменения средней сложности (рефакторинг, добавление фич)
    4-5 баллов - сложные изменения (архитектурные правки, сложная логика)

4. КОММЕНТАРИЙ - оцени наличие и структуру комментария:
    1 балл - комментарий плохо описывает происходящее в коде или его нет
    2 балла - минимальное описание
    3 балла - комментарий нормальный
    4 балла - комментарий объёмный, но не конкретный
    5 балл - комментарий полностью отражает все изменения в коде
    
ВАЖНО: 
- Оценивай КАЖДЫЙ критерий НЕЗАВИСИМО
- Подсчитывай РЕАЛЬНОЕ количество строк в коммите
- Не усредняй оценки между критериями
- Оценивай строго согласно метрикам

КОММИТ ДЛЯ АНАЛИЗА:
{diff_content}

Ответ СТРОГО в формате и ТОЛЬКО согласно формату:
Размер: X
Качество: Y
Сложность: Z
Комментарий: U
Сумма: X+Y+Z+U
"Сумма" - это просто одно число"""

        response = giga.chat(prompt)
        evaluation = response.choices[0].message.content

        print(f"   🤖 Оценка GigaChat для коммита {commit_hash[:8]}:")
        evaluation_lines = evaluation.split('\n')
        for line in evaluation_lines:
            if line.strip():
                print(f"      {line}")

        return evaluation

    except Exception as e:
        print(f"   ❌ Ошибка получения оценки от GigaChat: {e}")
        return None

def get_all_from_public(username_: str, show_commit_diff: bool = False, use_date_filter: bool = False):
    """Получить все репозитории и информацию из проекта public"""
    base_url = "https://gateway-codemetrics.saas.sferaplatform.ru/app/sourcecode/api/api/v2"

    username = "mapleleafrmsh@yandex.ru"
    password = "rOSjcKxPl7i2"

    credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json"
    }

    project_name = "public"

    # Всегда запрашиваем даты для фильтрации
    start_date, end_date = get_date_input()
    print(f"\n🔍 Поиск коммитов за период: {start_date} - {end_date}")

    print(f"\nПОЛУЧАЕМ ВСЕ ИЗ ПРОЕКТА '{project_name}':")

    try:
        # 1. Получить все репозитории проекта public
        print(f"\nПолучаем репозитории проекта '{project_name}'...")
        response = requests.get(f"{base_url}/projects/{project_name}/repos", headers=headers, verify=False)

        if response.status_code == 200:
            data = response.json()
            repos = data.get('data', [])

            if repos:
                print(f"Найдено репозиториев: {len(repos)}")

                for repo in repos:
                    repo_name = repo.get('name', 'Unknown')
                    repo_id = repo.get('id', 'Unknown')
                    print(f"\nРЕПОЗИТОРИЙ: {repo_name} (ID: {repo_id})")
                    print("=" * 50)

                    # Всегда используем фильтрацию по дате
                    commits = get_commits_by_date_range(
                        project_name,
                        repo_name,
                        start_date,
                        username_,
                        end_date,
                        headers,
                        show_diff=show_commit_diff
                    )
                    if not commits:
                        print("   ℹ️  Коммиты за указанный период не найдены")

            else:
                print(f"В проекте '{project_name}' нет репозиториев")
        else:
            print(f"Ошибка получения репозиториев: {response.status_code}")
            print(f"Текст ошибки: {response.text}")

    except Exception as e:
        print(f"Ошибка: {e}")


def save_commit_evaluation(commit_hash: str, evaluation_text: str, filename: str = "commit_evaluations.txt"):
    """Сохраняет оценку коммита в файл"""
    try:
        with open(filename, "a", encoding="utf-8") as f:
            f.write(f'"{commit_hash}"\n')

            # Извлекаем оценки из текста ответа
            lines = evaluation_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Размер:') or line.startswith('Качество:') or line.startswith(
                        'Сложность:') or line.startswith('Сумма:') or line.startswith('Комментарий:'):
                    f.write(f'"{line}"\n')

            f.write("~~~разделитель между коммитами~~~\n")
        print(f"   ✅ Оценка коммита {commit_hash[:8]} сохранена в файл")
    except Exception as e:
        print(f"   ❌ Ошибка сохранения оценки коммита: {e}")


def get_existing_commit_hashes(filename: str = "commit_evaluations.txt"):
    """Получает множество всех хэшей коммитов, которые уже есть в файле"""
    existing_hashes = set()
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            # Ищем все строки в кавычках (хэши коммитов)
            import re
            hash_matches = re.findall(r'"([a-fA-F0-9]{40})"', content)
            existing_hashes.update(hash_matches)
    except FileNotFoundError:
        # Файл не существует, значит хэшей еще нет
        pass
    except Exception as e:
        print(f"   ❌ Ошибка чтения файла с оценками: {e}")

    return existing_hashes

#метрики
def metrics(lines_count):
    K=0.2 # Коэф влияния сложности на качество
    difficult_metrics = lines_count*0.03*10 # сложность
    quality_metrics = (100-(difficult_metrics*K))/20 # качество
    # размер
    if lines_count > 80: size_metrics=5
    elif lines_count > 50: size_metrics=4
    elif lines_count > 20: size_metrics = 3
    elif lines_count > 10: size_metrics = 2
    else: size_metrics = 1
    return difficult_metrics, quality_metrics, size_metrics
def get_commit_evaluation_from_file(commit_hash: str, filename: str = "commit_evaluations.txt"):
    """Получает оценку коммита из файла, если она существует"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        # Разделяем содержимое на блоки по разделителям
        blocks = content.split("~~~разделитель между коммитами~~~")

        for block in blocks:
            lines = block.strip().split('\n')
            if lines and f'"{commit_hash}"' in lines[0]:
                # Нашли коммит, возвращаем все его оценки
                evaluation_lines = []
                for line in lines[1:]:  # Пропускаем первую строку с хэшем
                    line = line.strip()
                    if line and not line.startswith("~~~"):
                        evaluation_lines.append(line.strip('"'))
                return evaluation_lines

    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"   ❌ Ошибка чтения оценки из файла: {e}")


def get_commit_diff_decoded(project_name: str, repo_name: str, commit_sha: str, headers: dict):
    """Получить и декодировать diff коммита"""
    base_url = "https://gateway-codemetrics.saas.sferaplatform.ru/app/sourcecode/api/api/v2"

    try:
        response = requests.get(
            f"{base_url}/projects/{project_name}/repos/{repo_name}/commits/{commit_sha}/diff",
            headers=headers,
            verify=False
        )

        if response.status_code == 200:
            diff_data = response.json()
            data = diff_data.get('data', {})

            # Декодируем base64 content
            content_base64 = data.get('content', '')
            if content_base64:
                try:
                    # Декодируем base64 в строку
                    diff_content = base64.b64decode(content_base64).decode('utf-8')

                    # Анализ diff
                    file_changes, added_lines, deleted_lines, change_type, m = analyze_diff_content(diff_content)

                    print(f"   📊 Анализ коммита {commit_sha[:8]}:")
                    print(f"      {file_changes}")
                    print(f"      {added_lines}")
                    print(f"      {deleted_lines}")
                    print(f"      {change_type}")
                    return diff_content
                except Exception as decode_error:
                    print(f"      Ошибка декодирования diff: {decode_error}")
                    return None
            else:
                print(f"      Нет содержимого diff")
                return None

        else:
            print(f"      Ошибка получения diff: {response.status_code}")
            return None

    except Exception as e:
        print(f"      Ошибка при получении diff: {e}")
        return None


def analyze_diff_content(diff_content: str):
    """Анализировать содержимое diff"""
    lines = diff_content.split('\n')

    # Статистика по diff
    added_lines = 0
    deleted_lines = 0
    file_changes = 0
    current_file = None

    for line in lines:
        if line.startswith('diff --git'):
            file_changes += 1
            # Извлекаем имя файла
            parts = line.split(' ')
            if len(parts) >= 3:
                current_file = parts[2][2:]  # Убираем 'a/' в начале
        elif line.startswith('+') and not line.startswith('+++'):
            added_lines += 1
        elif line.startswith('-') and not line.startswith('---'):
            deleted_lines += 1

    # Определяем тип изменений
    if added_lines > 0 and deleted_lines == 0:
        change_type = "тип коммита: добавление"
    elif deleted_lines > 0 and added_lines == 0:
        change_type = "тип коммита: удаление"
    elif added_lines > 0 and deleted_lines > 0:
        change_type = "тип коммита: изменение"
    else:
        change_type = "тип коммита: без изменений"
    metric = metrics(abs(added_lines - deleted_lines))
    file_changes = f"Изменено файлов: {file_changes}"
    added_lines = f"Добавлено строк: {added_lines}"
    deleted_lines = f"Удалено строк: {deleted_lines}"

    return file_changes, added_lines, deleted_lines, change_type, metric


# Запуск
if __name__ == "__main__":
    print("🚀 АНАЛИЗ РЕПОЗИТОРИЕВ С GIGACHAT")
    print("=" * 50)

    # Всегда запрашиваем аккаунт
    use_filter_account = input("Введите интересующий вас аккаунт(почту): ")

    get_all_from_public(use_filter_account, show_commit_diff=True, use_date_filter=True)

    print("\nЗавершено получение всех данных из проекта 'public'!")