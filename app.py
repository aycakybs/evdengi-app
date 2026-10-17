import streamlit as st
import pandas as pd
import sys
import os

# Python'ın 'src' klasöründeki modülleri görebilmesi için yolu ekliyoruz
sys.path.append(os.path.abspath("src"))

# chore_service ve eski kurulum fonksiyonlarına veda ediyoruz!
# Artık her şeyi doğrudan yeni Supabase motorumuzdan çekiyoruz.
from database import supabase, ev_arkadaslarini_getir, gorevleri_getir, gorev_kaydet

# Sayfa yapılandırması
st.set_page_config(
    page_title="EvDengi - Ev İşi Takipçisi",
    page_icon="🏠",
    layout="wide"
)

# Başlık ve Açıklama
st.title("🏠 EvDengi: Ev İşi & Puan Takipçisi")
st.caption("Ev arkadaşları arasında adil, şeffaf ve puanlı iş bölümü")
st.divider()

# Yan Panel (Sidebar): Hızlı Görev Tamamlama
with st.sidebar:
    st.header("⚡ Hızlı Görev Tamamla")
    
    # 1. Ev arkadaşlarını Supabase'den çek
    roommates = ev_arkadaslarini_getir()
    roommate_options = {r["name"]: r["id"] for r in roommates}
    
    selected_roommate_name = st.selectbox("Görevi Kim Yaptı?", options=list(roommate_options.keys()))
    
    # 2. Görevleri Supabase'den çek
    chores = gorevleri_getir()
    chore_options = {f"{c['title']} (+{c['points']} puan)": c["id"] for c in chores}
    
    selected_chore_label = st.selectbox("Hangi İşi Yaptı?", options=list(chore_options.keys()))
    
    # Buton: Onayla
    if st.button("Kaydet ve Puanı Ekle", type="primary", use_container_width=True):
        r_id = roommate_options[selected_roommate_name]
        c_id = chore_options[selected_chore_label]
        
        # Yeni bulut veritabanımıza kaydediyoruz
        gorev_kaydet(chore_id=c_id, roommate_id=r_id)
        st.success(f"Tebrikler {selected_roommate_name}! Puanın başarıyla eklendi 🎉")
        st.rerun()  # Sayfayı yenileyerek yeni puanları anında göster

# Ana Ekranı 2 Kolona Bölelim
col_left, col_right = st.columns([1, 1], gap="large")

# Supabase'in gücü: Tüm geçmiş kayıtları, kimin yaptığı ve görev detaylarıyla tek seferde (JOIN) çekiyoruz
logs_response = supabase.table("chore_logs").select(
    "completed_at, roommates(name), chores(title, points)"
).order("completed_at", desc=True).execute()
all_logs = logs_response.data

# SOL KOLON: Liderlik Tablosu
with col_left:
    st.subheader("🏆 Liderlik Tablosu")
    
    # Liderlik verisini Pandas ile otomatik hesaplayalım
    leaderboard_dict = {r["name"]: {"Toplam Puan": 0, "Tamamlanan İş": 0} for r in roommates}
    
    for log in all_logs:
        r_name = log["roommates"]["name"]
        pts = log["chores"]["points"]
        leaderboard_dict[r_name]["Toplam Puan"] += pts
        leaderboard_dict[r_name]["Tamamlanan İş"] += 1
        
    lb_records = [
        {"İsim": k, "Toplam Puan": v["Toplam Puan"], "Tamamlanan İş": v["Tamamlanan İş"]} 
        for k, v in leaderboard_dict.items()
    ]
    df_lb = pd.DataFrame(lb_records).sort_values(by="Toplam Puan", ascending=False)
    
    st.dataframe(df_lb, use_container_width=True, hide_index=True)

    # Mini Bar Grafiği
    if not df_lb.empty and df_lb["Toplam Puan"].sum() > 0:
        st.bar_chart(df_lb.set_index("İsim")["Toplam Puan"])

# SAĞ KOLON: Son Hareketler & Görev Listesi
with col_right:
    st.subheader("🕒 Son Yapılanlar")
    
    recent_logs = all_logs[:5] # Sadece en son 5 işlemi al
    
    if recent_logs:
        for log in recent_logs:
            r_name = log["roommates"]["name"]
            c_title = log["chores"]["title"]
            pts = log["chores"]["points"]
            
            # Zamanı okunaklı hale getirelim (Örn: 2026-10-18 14:30)
            raw_time = log["completed_at"]
            clean_time = raw_time.split("T")[0] + " " + raw_time.split("T")[1][:5]
            
            st.info(
                f":violet[**{r_name}** — *{c_title} (+{pts} puan)*]  \n:violet[*{clean_time}*]",
                icon="🩷"
            )
    else:
        st.write("Henüz tamamlanmış bir görev yok.")

    st.divider()
    
    # Bilgi akordiyonu
    with st.expander("📋 Puan Cetveli ve Görevler"):
        chores_data = [
            {"Kategori": c["category"], "Görev": c["title"], "Puan": c["points"]}
            for c in chores
        ]
        st.table(pd.DataFrame(chores_data))