import google.generativeai as genai
import requests
import sys

# ==========================================
# 1. KONFIGURASI (CREDENTIALS)
# ==========================================
# API Keys (Sesuai permintaan, hardcoded untuk demo)
GEMINI_API_KEY = 'AIzaSyDXr6zd7wkAZm1HGOAkAAPK-igMc29n37E'
FONNTE_API_TOKEN = 'YojmEUBfp9T7Zt8N9VBm'
YOUR_PHONE_NUMBER = '6289698035966' # Nomor tujuan (Ibu/Pasien)

# Konfigurasi Model AI
MODEL_NAME = 'gemini-2.5-flash' # Menggunakan model flash agar cepat dan hemat biaya

# ==========================================
# 2. SISTEM OTAK AI (SYSTEM PROMPT)
# ==========================================
def get_gemini_response(user_question):
    """
    Fungsi untuk meminta saran kesehatan kepada Gemini
    dengan persona ahli stunting.
    """
    if not GEMINI_API_KEY:
        return "Error: API Key Gemini belum diisi."

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)

        # Instruksi kepribadian bot (Persona)
        system_instruction = """
        Anda adalah 'Bidan AI', asisten virtual cerdas yang fokus pada PENCEGAHAN STUNTING.
        
        Tugas Anda adalah memberikan edukasi dan saran kepada calon ibu dan ibu hamil.
        Cakupan pengetahuan Anda meliputi:
        1. Pra-konsepsi (Persiapan sebelum hamil, gizi calon pengantin).
        2. Masa Kehamilan (Nutrisi Trimester 1-3, Tablet Tambah Darah).
        3. Pasca-lahiran & Menyusui (ASI Eksklusif, MPASI, Sanitasi).
        
        Aturan Menjawab:
        - Gaya bahasa: Ramah, empatik, seperti bidan sahabat keluarga, namun tetap ilmiah.
        - Format: Gunakan poin-poin atau paragraf pendek agar mudah dibaca di WhatsApp.
        - Selalu tekankan pentingnya "1000 Hari Pertama Kehidupan".
        - Jika pertanyaan mengarah ke kondisi gawat darurat medis, sarankan segera ke Fasilitas Kesehatan.
        - Batasi jawaban maksimal 150-200 kata agar tidak terlalu panjang di chat.
        """

        # Menggabungkan instruksi sistem dengan pertanyaan user
        full_prompt = f"{system_instruction}\n\nPertanyaan User: {user_question}\n\nJawaban Bidan AI:"
        
        response = model.generate_content(full_prompt)
        return response.text.strip()

    except Exception as e:
        return f"Maaf, sistem AI sedang sibuk. Error: {str(e)}"

# ==========================================
# 3. FUNGSI KIRIM WHATSAPP (FONNTE)
# ==========================================
def send_whatsapp_message(message_content):
    """
    Mengirimkan pesan hasil jawaban AI ke WhatsApp pengguna via Fonnte
    """
    if not FONNTE_API_TOKEN or not YOUR_PHONE_NUMBER:
        print("Error: Token Fonnte atau Nomor HP belum diset.")
        return

    url = "https://api.fonnte.com/send"
    
    # Payload Fonnte
    payload = {
        'target': YOUR_PHONE_NUMBER,
        'message': message_content,
        'countryCode': '62' # Kode negara Indonesia
    }
    
    headers = {
        'Authorization': FONNTE_API_TOKEN
    }

    try:
        print("⏳ Sedang mengirim ke WhatsApp...")
        response = requests.post(url, headers=headers, data=payload)
        print(f"✅ Status Pengiriman: {response.text}")
    except Exception as e:
        print(f"❌ Gagal mengirim WA: {e}")

# ==========================================
# 4. MAIN LOOP (INTERAKTIF)
# ==========================================
def main():
    print("\n" + "="*50)
    print("   🤖 CHATBOT PENCEGAHAN STUNTING (DEMO)   ")
    print("="*50)
    print("Ketik pertanyaan Anda tentang kehamilan/gizi anak.")
    print("Ketik 'exit' atau 'keluar' untuk berhenti.\n")

    while True:
        try:
            # 1. Input Pertanyaan (Simulasi pesan masuk)
            user_input = input("👩 Ibu Bertanya: ")
            
            if user_input.lower() in ['exit', 'keluar', 'stop']:
                print("Terima kasih, sehat selalu! 👋")
                break
            
            if not user_input.strip():
                continue

            # 2. Proses AI
            print("🤔 Bidan AI sedang mengetik...")
            ai_response = get_gemini_response(user_input)
            
            # 3. Tampilkan di Terminal (Log)
            print("-" * 30)
            print(f"💊 Jawaban AI:\n{ai_response}")
            print("-" * 30)

            # 4. Kirim ke WhatsApp Target
            send_whatsapp_message(ai_response)
            print("\n")

        except KeyboardInterrupt:
            print("\nProgram dihentikan paksa.")
            sys.exit()

if __name__ == "__main__":
    main()