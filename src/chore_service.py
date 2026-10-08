from datetime import datetime
from database import get_connection


def get_all_roommates():
    """Tüm ev arkadaşlarını döndürür."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM roommates ORDER BY name ASC")
    roommates = cursor.fetchall()
    conn.close()
    return roommates

def get_all_chores():
    """Tüm görevleri döndürür."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category, points FROM chores ORDER BY category , title")
    chores = cursor.fetchall()
    conn.close()
    return chores






def complete_chore(roommate_id: int, chore_id: int):
    """
    Bir ev işinin tamamlandığını kaydeder sistem tarih ve saati otomatik ekler
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Şu anki zaman damgası (timestamp)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
    INSERT INTO chore_logs (chore_id, roommate_id, completed_at) 
    VALUES (?, ?, ?)
    """, (chore_id, roommate_id, now))

    conn.commit()
    conn.close()
    return True


def get_leaderboard():
    """
    Kimin kaç puanı oldugunu hesaplar
    SQL'in LEFT JOIN ve SUM fonksiyonları ile henüz hiç iş yapmamış
    kişilerde 0 puanla dahil olur
    """

    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            r.id,
            r.name,
            COALESCE(SUM(c.points), 0) AS total_points,
            COUNT(cl.id) AS total_chores_done
        FROM roommates r
        LEFT JOIN chore_logs cl ON r.id = cl.roommate_id
        LEFT JOIN chores c ON cl.chore_id = c.id
        GROUP BY r.id, r.name
        ORDER BY total_points DESC, total_chores_done DESC
    """
    cursor.execute(query)
    leaderboard = cursor.fetchall()
    conn.close()
    return leaderboard


def get_recent_activities(limit: int = 5):
    conn = get_connection()
    cursor = conn.cursor()
    
    # "AS points" ve "AS completed_at" ekleyerek isimleri sabitliyoruz
    query = """
        SELECT 
            r.name AS roommate_name,
            c.title AS chore_title,
            c.points AS points,
            cl.completed_at AS completed_at
        FROM chore_logs cl
        JOIN roommates r ON cl.roommate_id = r.id
        JOIN chores c ON cl.chore_id = c.id
        ORDER BY cl.completed_at DESC
        LIMIT ?;
    """
    cursor.execute(query, (limit,))
    logs = cursor.fetchall()
    conn.close()
    return logs


