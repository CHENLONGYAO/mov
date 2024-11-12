import lib


def main():
    conn = lib.connect_db()
    lib.create_table(conn)

    while True:
        print('\n----- 電影管理系統 -----')
        print('1. 匯入電影資料檔')
        print('2. 查詢電影')
        print('3. 新增電影')
        print('4. 修改電影')
        print('5. 刪除電影')
        print('6. 匯出電影')
        print('7. 離開系統')
        print('------------------------')
        choice = input('請選擇操作選項 (1-7): ').strip()

        if choice == '1':
            lib.import_movies(conn)
        elif choice == '2':
            yn = input('查詢全部電影嗎？(y/n): ').lower()
            if yn == 'y':
                movies = lib.search_movies(conn)
                lib.list_rpt(movies)
            else:
                title = input('請輸入電影名稱: ').strip()
                movies = lib.search_movies(conn, title)
                lib.list_rpt(movies)
        elif choice == '3':
            lib.add_movie(conn)
        elif choice == '4':
            lib.modify_movie(conn)
        elif choice == '5':
            lib.delete_movies(conn)
        elif choice == '6':
            lib.export_movies(conn)
        elif choice == '7':
            print('系統已退出。')
            conn.close()
            break
        else:
            print('無效的選項，請重新輸入。')


if __name__ == '__main__':
    main()
