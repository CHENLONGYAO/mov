import os
import sqlite3
import json
from typing import List, Dict, Union
import unicodedata

DB_PATH = 'movies.db'
JSON_IN_PATH = 'movies.json'
JSON_OUT_PATH = 'exported.json'


def connect_db() -> sqlite3.Connection:
    """連接到 SQLite 資料庫，若不存在則自動建立。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 查詢結果以字典形式返回
    return conn


def create_table(conn: sqlite3.Connection) -> None:
    """建立 movies 資料表（若不存在）。"""
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                director TEXT NOT NULL,
                genre TEXT NOT NULL,
                year INTEGER NOT NULL,
                rating REAL CHECK (rating >= 1.0 AND rating <= 10.0)
            )
        ''')


def get_display_width(s: str) -> int:
    """計算字串在終端機顯示時的寬度。"""
    width = 0
    for ch in s:
        if unicodedata.east_asian_width(ch) in ('F', 'W', 'A'):
            width += 2  # 全形字符寬度為2
        else:
            width += 1  # 半形字符寬度為1
    return width


def pad_string(s: str, total_width: int) -> str:
    """根據顯示寬度來填充字串，使其達到指定的總寬度。"""
    padding = total_width - get_display_width(s)
    return s + ' ' * max(padding, 0)


def list_rpt(movies: List[sqlite3.Row]) -> None:
    """格式化列印電影列表。"""
    if not movies:
        print('查無資料')
        return
    print()
    headers = ['電影名稱', '導演', '類型', '上映年份', '評分']
    widths = [20, 24, 12, 10, 6]  # 設定每個欄位的顯示寬度
    header_line = ''.join(pad_string(h, w) for h, w in zip(headers, widths))
    print(header_line)
    print('-' * sum(widths))
    for movie in movies:
        row = [
            pad_string(movie['title'], widths[0]),
            pad_string(movie['director'], widths[1]),
            pad_string(movie['genre'], widths[2]),
            pad_string(str(movie['year']), widths[3]),
            pad_string(str(movie['rating']), widths[4])
        ]
        print(''.join(row))


def import_movies(conn: sqlite3.Connection) -> None:
    """從 movies.json 匯入電影資料到資料庫。"""
    try:
        with open(JSON_IN_PATH, 'r', encoding='utf-8') as f:
            movies = json.load(f)
        with conn:
            conn.executemany('''
                INSERT INTO movies (title, director, genre, year, rating)
                VALUES (?, ?, ?, ?, ?)
            ''', [(movie['title'], movie['director'], movie['genre'],
                   movie['year'], movie['rating']) for movie in movies])
        print('電影已匯入')
    except FileNotFoundError:
        print('找不到檔案...')
    except json.JSONDecodeError:
        print('JSON 解析錯誤')
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    except Exception as e:
        print(f'發生其它錯誤 {e}')


def search_movies(conn: sqlite3.Connection, title: str = '') -> List[sqlite3.Row]:
    """查詢電影，可選擇依電影名稱過濾。"""
    try:
        with conn:
            if title:
                cursor = conn.execute(
                    "SELECT * FROM movies WHERE title LIKE ?", (f'%{title}%',))
            else:
                cursor = conn.execute("SELECT * FROM movies")
            movies = cursor.fetchall()
            return movies
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
        return []
    except Exception as e:
        print(f'發生其它錯誤 {e}')
        return []


def add_movie(conn: sqlite3.Connection) -> None:
    """新增一部電影到資料庫。"""
    title = input('電影名稱: ').strip()
    director = input('導演: ').strip()
    genre = input('類型: ').strip()
    try:
        year = int(input('上映年份: ').strip())
        rating = float(input('評分 (1.0 - 10.0): ').strip())
        if not (1.0 <= rating <= 10.0):
            print('評分需在 1.0 到 10.0 之間')
            return
        with conn:
            conn.execute('''
                INSERT INTO movies (title, director, genre, year, rating)
                VALUES (?, ?, ?, ?, ?)
            ''', (title, director, genre, year, rating))
        print('電影已新增')
    except ValueError:
        print('年份或評分格式錯誤')
    except sqlite3.DatabaseError as e:
        print(f"資料庫操作發生錯誤: {e}")
    except Exception as e:
        print(f'發生其它錯誤 {e}')


def modify_movie(conn: sqlite3.Connection) -> None:
    """修改現有的電影資料。"""
    title = input('請輸入要修改的電影名稱: ').strip()
    movies = search_movies(conn, title)
    if not movies:
        print('查無資料')
        return
    list_rpt(movies)
    movie = movies[0]  # 假設修改第一個匹配的電影
    new_title = input('請輸入新的電影名稱 (若不修改請直接按 Enter): ').strip()
    new_director = input('請輸入新的導演 (若不修改請直接按 Enter): ').strip()
    new_genre = input('請輸入新的類型 (若不修改請直接按 Enter): ').strip()
    new_year = input('請輸入新的上映年份 (若不修改請直接按 Enter): ').strip()
    new_rating = input('請輸入新的評分 (1.0 - 10.0) (若不修改請直接按 Enter): ').strip()
    update_fields = {}
    if new_title:
        update_fields['title'] = new_title
    if new_director:
        update_fields['director'] = new_director
    if new_genre:
        update_fields['genre'] = new_genre
    if new_year:
        try:
            update_fields['year'] = int(new_year)
        except ValueError:
            print('年份格式錯誤')
            return
    if new_rating:
        try:
            rating_value = float(new_rating)
            if not (1.0 <= rating_value <= 10.0):
                print('評分需在 1.0 到 10.0 之間')
                return
            update_fields['rating'] = rating_value
        except ValueError:
            print('評分格式錯誤')
            return
    if update_fields:
        set_clause = ', '.join(f"{k} = ?" for k in update_fields.keys())
        params = list(update_fields.values()) + [movie['id']]
        try:
            with conn:
                conn.execute(f'''
                    UPDATE movies SET {set_clause} WHERE id = ?
                ''', params)
            print('資料已修改')
        except sqlite3.DatabaseError as e:
            print(f"資料庫操作發生錯誤: {e}")
        except Exception as e:
            print(f'發生其它錯誤 {e}')
    else:
        print('未作任何修改')


def delete_movies(conn: sqlite3.Connection) -> None:
    """從資料庫中刪除電影。"""
    all_delete = input('刪除全部電影嗎？(y/n): ').lower()
    if all_delete == 'y':
        confirm = input('確定要刪除全部電影嗎？(y/n): ').lower()
        if confirm == 'y':
            try:
                with conn:
                    conn.execute('DELETE FROM movies')
                print('全部電影已刪除')
            except sqlite3.DatabaseError as e:
                print(f"資料庫操作發生錯誤: {e}")
            except Exception as e:
                print(f'發生其它錯誤 {e}')
        else:
            print('取消刪除')
    else:
        title = input('請輸入要刪除的電影名稱: ').strip()
        movies = search_movies(conn, title)
        if not movies:
            print('查無資料')
            return
        list_rpt(movies)
        confirm = input('是否要刪除(y/n): ').lower()
        if confirm == 'y':
            try:
                ids_to_delete = [movie['id'] for movie in movies]
                with conn:
                    conn.executemany(
                        'DELETE FROM movies WHERE id = ?', [(id_,) for id_ in ids_to_delete])
                print('電影已刪除')
            except sqlite3.DatabaseError as e:
                print(f"資料庫操作發生錯誤: {e}")
            except Exception as e:
                print(f'發生其它錯誤 {e}')
        else:
            print('取消刪除')


def export_movies(conn: sqlite3.Connection) -> None:
    """將電影資料匯出至 exported.json。"""
    all_export = input('匯出全部電影嗎？(y/n): ').lower()
    if all_export == 'y':
        movies = search_movies(conn)
    else:
        title = input('請輸入要匯出的電影名稱: ').strip()
        movies = search_movies(conn, title)
    if not movies:
        print('查無資料')
        return
    movies_list = [dict(movie) for movie in movies]
    try:
        with open(JSON_OUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(movies_list, f, ensure_ascii=False, indent=4)
        print(f'電影資料已匯出至 {JSON_OUT_PATH}')
    except Exception as e:
        print(f'發生錯誤: {e}')
