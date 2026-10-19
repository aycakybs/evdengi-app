import streamlit as st
import random
import string
from supabase import create_client, Client

# Supabase bağlantı ayarları
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase: Client = create_client(supabase_url, supabase_key)

def giris_yap(email, sifre):
    return supabase.auth.sign_in_with_password({"email": email, "password": sifre})

def kayit_ol(email, sifre):
    return supabase.auth.sign_up({"email": email, "password": sifre})

def oturum_ayarla(access_token, refresh_token):
    try:
        supabase.auth.set_session(access_token, refresh_token)
    except:
        pass

def kullanicinin_evini_getir(user_id):
    # Önce kişinin kurucu olduğu evi ara
    ev = supabase.table("households").select("*").eq("user_id", user_id).execute()
    if ev.data:
        return ev.data
    
    # Eğer kurucu değilse, davet koduyla katıldığı (roommates listesinde olduğu) evi ara
    oda_arkadasi = supabase.table("roommates").select("household_id").eq("user_id", user_id).execute()
    if oda_arkadasi.data:
        h_id = oda_arkadasi.data[0]["household_id"]
        ev_katildigi = supabase.table("households").select("*").eq("id", h_id).execute()
        return ev_katildigi.data
        
    return []

def ev_ve_arkadaslari_olustur(ev_adi, user_id, kurucu_adi):
    # 6 haneli rastgele ve havalı bir davet kodu üret
    davet_kodu = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    ev_data = {"name": ev_adi, "user_id": user_id, "invite_code": davet_kodu}
    ev_response = supabase.table("households").insert(ev_data).execute()
    yeni_ev_id = ev_response.data[0]["id"]
    
    # Evi kuran kişiyi de ev arkadaşları (roommates) listesine otomatik ekle
    supabase.table("roommates").insert({"household_id": yeni_ev_id, "name": kurucu_adi, "user_id": user_id}).execute()
        
    sablonlar = [
        {"household_id": yeni_ev_id, "title": "Bulaşık makinesini boşaltmak", "category": "Mutfak", "points": 10},
        {"household_id": yeni_ev_id, "title": "Çöpü atmak", "category": "Genel", "points": 5},
        {"household_id": yeni_ev_id, "title": "Evi süpürmek", "category": "Temizlik", "points": 20}
    ]
    supabase.table("chores").insert(sablonlar).execute()
    
    return yeni_ev_id

def eve_katil(davet_kodu, user_id, kullanici_adi):
    # Kodu kullanarak evi bul
    ev_response = supabase.table("households").select("*").eq("invite_code", davet_kodu).execute()
    if not ev_response.data:
        raise Exception("Geçersiz davet kodu! Kodu kontrol edip tekrar deneyin.")
    
    ev_id = ev_response.data[0]["id"]
    # Kullanıcıyı o evin roommates listesine ekle
    supabase.table("roommates").insert({"household_id": ev_id, "name": kullanici_adi, "user_id": user_id}).execute()
    return ev_id

def ev_arkadaslarini_getir():
    response = supabase.table("roommates").select("*").execute()
    return response.data

def gorevleri_getir():
    response = supabase.table("chores").select("*").execute()
    return response.data

def gorev_kaydet(chore_id, roommate_id):
    data = {"chore_id": chore_id, "roommate_id": roommate_id}
    response = supabase.table("chore_logs").insert(data).execute()
    return response.data