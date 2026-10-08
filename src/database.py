import sqlite3
from datetime import datetime

# veritabanı dosyasının adı
DB_NAME = 'evdengi.db'

def get_connection():
    """Veritabanı bağlantısı oluşturur ve row_factory ayarı sayesinde verileri sadece tuple olarak değil sözlük gibidöndürür."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(): 
    """Veritabanını başlatır ve gerekli tabloları oluşturur. Uygulama ilk kez çalıştığında bi kez çalışır"""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. ev arkları tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS roommates(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
    """)

    # 2. Görevler Tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 10
        );
    """)

    # 3. yapılan işlerin kaydı tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chore_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chore_id INTEGER NOT NULL,
            roommate_id INTEGER NOT NULL,
            completed_at TIMESTAMP NOT NULL,
            FOREIGN KEY (chore_id) REFERENCES chores(id),
            FOREIGN KEY (roommate_id) REFERENCES roommates(id)
        );
    """)

    # değişiklikleri kaydetip ve bağlantıyı kapatma
    conn.commit()
    conn.close()

def seed_initial_data():
    """
    test etmek için veritabanına 3 ev arkadası ve biraz temel ev işi ekleyelim"""

    conn = get_connection()
    cursor = conn.cursor()

    # daha önce eklenmiş ev arkadası yoksa ekle
    cursor.execute("SELECT COUNT(*) FROM roommates")
    if cursor.fetchone()[0] == 0:
        default_roommates = [("Ayça",), ("Gülce",), ("Şeyma",)]
        cursor.executemany("INSERT INTO roommates (name) VALUES (?)", default_roommates)

    # görev ekleme
    cursor.execute("SELECT COUNT(*) FROM chores")
    if cursor.fetchone()[0] == 0:
        default_chores = [
            ("Bulaşık makinesini boşaltmak", "Mutfak", 10),
            ("Bulaşıkları yerleştirmek / elde yıkamak", "Mutfak", 15),
            ("Çöpü atmak", "Genel", 5),
            ("Evi süpürmek & silmek", "Temizlik", 30),
            ("Banyouyu Temzilemek", "Temizlik", 35),
            ("Market alışverişi yapmak", "Alışveriş", 25),
        ]
        cursor.executemany(
            "INSERT INTO chores (title, category, points) VALUES (?, ?, ?)",
            default_chores
        )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Dosya doğrudan çalıştırdığımızda veritabanını kurup doldursun
    init_db()
    seed_initial_data()
    print("Veritabanu ve örnek veriler başarıyla oluşturuldu")