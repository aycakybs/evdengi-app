import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath("src"))

from database import (
    supabase, ev_arkadaslarini_getir, gorevleri_getir, gorev_kaydet, 
    giris_yap, kayit_ol, oturum_ayarla, 
    kullanicinin_evini_getir, ev_ve_arkadaslari_olustur, eve_katil
)

st.set_page_config(page_title="EvDengi - Ev İşi Takipçisi", page_icon="🏠", layout="wide")

if "kullanici" not in st.session_state:
    st.session_state.kullanici = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None

if st.session_state.access_token:
    oturum_ayarla(st.session_state.access_token, st.session_state.refresh_token)

# GİRİŞ YAPMAMIŞSA
if st.session_state.kullanici is None:
    st.title("🏠 EvDengi'ye Hoş Geldiniz")
    st.caption("Lütfen devam etmek için giriş yapın veya yeni bir ev hesabı oluşturun.")
    
    tab1, tab2 = st.tabs(["Giriş Yap", "Yeni Kayıt Ol"])
    
    with tab1:
        g_email = st.text_input("E-posta", key="g_email")
        g_sifre = st.text_input("Şifre", type="password", key="g_sifre")
        if st.button("Giriş", type="primary"):
            try:
                response = giris_yap(g_email, g_sifre)
                st.session_state.kullanici = response.user
                st.session_state.access_token = response.session.access_token
                st.session_state.refresh_token = response.session.refresh_token
                st.rerun()
            except:
                st.error("Giriş başarısız. Lütfen e-posta ve şifrenizi kontrol edin.")
                
    with tab2:
        k_email = st.text_input("E-posta", key="k_email")
        k_sifre = st.text_input("Şifre (En az 6 karakter)", type="password", key="k_sifre")
        if st.button("Kayıt Ol", type="primary"):
            try:
                kayit_ol(k_email, k_sifre)
                st.success("Kayıt başarılı! Şimdi 'Giriş Yap' sekmesinden giriş yapabilirsiniz.")
            except:
                st.error("Kayıt başarısız. Bu adres kayıtlı olabilir.")

# GİRİŞ YAPMIŞSA
else:
    user_id = st.session_state.kullanici.id
    kullanici_evi = kullanicinin_evini_getir(user_id)
    
    col_baslik, col_cikis = st.columns([8, 1])
    with col_baslik:
        st.title("🏠 EvDengi: Ev İşi & Puan Takipçisi")
    with col_cikis:
        if st.button("🚪 Çıkış Yap"):
            st.session_state.kullanici = None
            st.session_state.access_token = None
            st.session_state.refresh_token = None
            st.rerun()
            
    st.divider()

    # DURUM 1: HENÜZ BİR EV YOKSA (KUR & KATIL EKRANI)
    if not kullanici_evi:
        st.info("👋 Hoş geldin! Görünüşe göre henüz bir ev kurmamışsın veya mevcut bir eve katılmamışsın.")
        
        tab_kur, tab_katil = st.tabs(["🛠️ Kendi Evini Kur", "🤝 Davet Koduyla Katıl"])
        
        with tab_kur:
            ev_adi = st.text_input("Evine bir isim ver (Örn: Bizim Ev)", key="ev_adi_input")
            kurucu_adi = st.text_input("Senin Adın Ne?", key="kurucu_adi_input")
            
            if st.button("Evi Kur ve Başla", type="primary"):
                if ev_adi and kurucu_adi:
                    try:
                        ev_ve_arkadaslari_olustur(ev_adi, user_id, kurucu_adi)
                        st.success("Evin kuruldu! Ana ekrana yönlendiriliyorsun...")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
                else:
                    st.warning("Lütfen ev adını ve adınızı girin.")
                    
        with tab_katil:
            davet_kodu = st.text_input("Ev Arkadaşının Verdiği Davet Kodu")
            katilimci_adi = st.text_input("Senin Adın Ne?", key="katilimci_adi_input")
            
            if st.button("Eve Katıl", type="primary"):
                if davet_kodu and katilimci_adi:
                    try:
                        eve_katil(davet_kodu.upper(), user_id, katilimci_adi)
                        st.success("Eve başarıyla katıldın! Yönlendiriliyorsun...")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Lütfen kodu ve adınızı girin.")

    # DURUM 2: EVİ VARSA (ANA UYGULAMA)
    else:
        roommates = ev_arkadaslarini_getir()
        chores = gorevleri_getir()
        
        logs_response = supabase.table("chore_logs").select(
            "completed_at, roommates(name), chores(title, points)"
        ).order("completed_at", desc=True).execute()
        all_logs = logs_response.data

        with st.sidebar:
            # DAVET KODUNU GÖSTER
            aktif_kod = kullanici_evi[0].get('invite_code')
            if aktif_kod:
                st.info(f"**Ev Davet Kodunuz:**\n### {aktif_kod}")
                st.caption("Bu kodu ev arkadaşlarına göndererek onları da bu eve dahil edebilirsin.")
            
            st.divider()
            st.header("⚡ Hızlı Görev Tamamla")
            
            if not roommates or not chores:
                st.warning("Evinizde henüz ev arkadaşı veya görev yok.")
            else:
                roommate_options = {r["name"]: r["id"] for r in roommates}
                selected_roommate_name = st.selectbox("Görevi Kim Yaptı?", options=list(roommate_options.keys()))
                
                chore_options = {f"{c['title']} (+{c['points']} puan)": c["id"] for c in chores}
                selected_chore_label = st.selectbox("Hangi İşi Yaptı?", options=list(chore_options.keys()))
                
                if st.button("Kaydet ve Puanı Ekle", type="primary", use_container_width=True):
                    r_id = roommate_options[selected_roommate_name]
                    c_id = chore_options[selected_chore_label]
                    gorev_kaydet(chore_id=c_id, roommate_id=r_id)
                    st.success(f"Puan başarıyla eklendi 🎉")
                    st.rerun()

        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.subheader("🏆 Liderlik Tablosu")
            if not roommates:
                st.warning("Bu evde kimse yok.")
            else:
                leaderboard_dict = {r["name"]: {"Toplam Puan": 0, "Tamamlanan İş": 0} for r in roommates}
                for log in all_logs:
                    r_name = log["roommates"]["name"]
                    pts = log["chores"]["points"]
                    leaderboard_dict[r_name]["Toplam Puan"] += pts
                    leaderboard_dict[r_name]["Tamamlanan İş"] += 1
                    
                lb_records = [{"İsim": k, "Toplam Puan": v["Toplam Puan"], "Tamamlanan İş": v["Tamamlanan İş"]} for k, v in leaderboard_dict.items()]
                df_lb = pd.DataFrame(lb_records)
                
                if not df_lb.empty:
                    df_lb = df_lb.sort_values(by="Toplam Puan", ascending=False)
                    st.dataframe(df_lb, use_container_width=True, hide_index=True)
                    if df_lb["Toplam Puan"].sum() > 0:
                        st.bar_chart(df_lb.set_index("İsim")["Toplam Puan"])

        with col_right:
            st.subheader("🕒 Son Yapılanlar")
            recent_logs = all_logs[:5]
            if recent_logs:
                for log in recent_logs:
                    r_name = log["roommates"]["name"]
                    c_title = log["chores"]["title"]
                    pts = log["chores"]["points"]
                    clean_time = log["completed_at"].split("T")[0] + " " + log["completed_at"].split("T")[1][:5]
                    st.info(f":violet[**{r_name}** — *{c_title} (+{pts} puan)*]  \n:violet[*{clean_time}*]", icon="🩷")
            else:
                st.write("Henüz tamamlanmış bir görev yok.")

            st.divider()
            with st.expander("📋 Puan Cetveli ve Görevler"):
                if chores:
                    st.table(pd.DataFrame([{"Kategori": c["category"], "Görev": c["title"], "Puan": c["points"]} for c in chores]))
                else:
                    st.write("Görev listesi boş.")