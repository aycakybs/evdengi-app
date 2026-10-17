import streamlit as st
from supabase import create_client, Client

# Supabase bağlantı ayarları (Gizli kasamızdan okunuyor)
supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase: Client = create_client(supabase_url, supabase_key)

def ev_arkadaslarini_getir():
    """Veritabanından ev arkadaşlarının listesini çeker."""
    response = supabase.table("roommates").select("*").execute()
    return response.data

def gorevleri_getir():
    """Veritabanından mevcut görevleri çeker."""
    response = supabase.table("chores").select("*").execute()
    return response.data

def gorev_kaydet(chore_id, roommate_id):
    """Yapılan görevi buluttaki günlüğe (chore_logs) kaydeder."""
    # Tarihi ve saati Supabase sunucusu otomatik (NOW) ekleyeceği için sadece ID'leri yolluyoruz.
    data = {
        "chore_id": chore_id,
        "roommate_id": roommate_id
    }
    response = supabase.table("chore_logs").insert(data).execute()
    return response.data