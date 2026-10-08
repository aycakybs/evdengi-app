import streamlit as st
import pandas as pd
import sys
import os

# Python'ın 'src' klasöründeki modülleri görebilmesi için yolu ekliyoruz
sys.path.append(os.path.abspath("src"))

from database import init_db, seed_initial_data
from chore_service import (
    get_all_roommates,
    get_all_chores,
    complete_chore,
    get_leaderboard,
    get_recent_activities
)

# Sayfa yapılandırması
st.set_page_config(
    page_title="EvDengi - Ev İşi Takipçisi",
    page_icon="🏠",
    layout="wide"
)

# Veritabanının hazır olduğundan emin olalım
init_db()
seed_initial_data()

# Başlık ve Açıklama
st.title("🏠 EvDengi: Ev İşi & Puan Takipçisi")
st.caption("Ev arkadaşları arasında adil, şeffaf ve puanlı iş bölümü")

st.divider()

# Yan Panel (Sidebar): Hızlı Görev Tamamlama
with st.sidebar:
    st.header("⚡ Hızlı Görev Tamamla")
    
    # 1. Ev arkadaşlarını çek
    roommates = get_all_roommates()
    roommate_options = {r["name"]: r["id"] for r in roommates}
    
    selected_roommate_name = st.selectbox(
        "Görevi Kim Yaptı?",
        options=list(roommate_options.keys())
    )
    
    # 2. Görevleri çek
    chores = get_all_chores()
    chore_options = {f"{c['title']} (+{c['points']} puan)": c["id"] for c in chores}
    
    selected_chore_label = st.selectbox(
        "Hangi İşi Yaptı?",
        options=list(chore_options.keys())
    )
    
    # Buton: Onayla
    if st.button("Kaydet ve Puanı Ekle", type="primary", use_container_width=True):
        r_id = roommate_options[selected_roommate_name]
        c_id = chore_options[selected_chore_label]
        
        complete_chore(roommate_id=r_id, chore_id=c_id)
        st.success(f"Tebrikler {selected_roommate_name}! Puanın başarıyla eklendi 🎉")
        st.rerun()  # Sayfayı yenileyerek yeni puanları anında göster

# Ana Ekranı 2 Kolona Bölelim
col_left, col_right = st.columns([1, 1], gap="large")

# SOL KOLON: Liderlik Tablosu
with col_left:
    st.subheader("🏆 Liderlik Tablosu")
    leaderboard_data = get_leaderboard()
    
    # Veriyi tablo haline getirelim
    lb_records = []
    for row in leaderboard_data:
        lb_records.append({
            "İsim": row["name"],
            "Toplam Puan": row["total_points"],
            "Tamamlanan İş": row["total_chores_done"]
        })
    
    df_lb = pd.DataFrame(lb_records)
    st.dataframe(df_lb, use_container_width=True, hide_index=True)

    # Mini Bar Grafiği (Puan dağılımı görseli)
    if not df_lb.empty:
        st.bar_chart(df_lb.set_index("İsim")["Toplam Puan"])

# SAĞ KOLON: Son Hareketler & Görev Listesi
with col_right:
    st.subheader("🕒 Son Yapılanlar")
    recent_logs = get_recent_activities(limit=5)
    
    if recent_logs:
        for log in recent_logs:
            # HTML etiketlerini sildik, yerine * işareti ile eğik yazı yaptık
            # Her satırı ayrı ayrı :violet[ ] içine alıyoruz
                st.info(
                    f":violet[**{log['roommate_name']}** — *{log['chore_title']}* (+{log['points']} puan)]  \n"
                    f":violet[*{log['completed_at']}*]",
                    icon="🩷"
                )
    else:
        st.write("Henüz tamamlanmış bir görev yok.")

    st.divider()
    
    # Bilgi akordiyonu
    with st.expander("📋 Puan Cetveli ve Görevler"):
        chores_list = get_all_chores()
        chores_data = [
            {"Kategori": c["category"], "Görev": c["title"], "Puan": c["points"]}
            for c in chores_list
        ]
        st.table(pd.DataFrame(chores_data))