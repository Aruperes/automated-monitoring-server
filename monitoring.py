import os
import re
import google.generativeai as genai
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# --- 1. KONFIGURASI ---
# (Ubah nilai-nilai ini sesuai kebutuhan Anda)

# Lokasi file log SSH
# Ubuntu/Debian: '/var/log/auth.log'
# CentOS/RHEL/Fedora: '/var/log/secure'
LOG_FILE_PATH = '/var/log/auth.log' 

# Jendela waktu untuk diperiksa (dalam menit)
TIME_WINDOW_MINUTES = 10

# Ambang batas kegagalan sebelum memicu peringatan
FAILURE_THRESHOLD = 2

# Kunci API dan Konfigurasi
GEMINI_API_KEY = 'AIzaSyDXr6zd7wkAZm1HGOAkAAPK-igMc29n37E'  
FONNTE_API_TOKEN = 'YojmEUBfp9T7Zt8N9VBm'     
YOUR_PHONE_NUMBER = '6289698035966'

# Pola Regex untuk mendeteksi kegagalan login
# Ini menangkap timestamp, dan alamat IP
LOG_PATTERN = re.compile(
    r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}).*sshd\[\d+\]: Failed password for .* from ([\d\.]+) port'
)

# --- 2. FUNGSI API (GEMINI & FONNTE) ---

def setup_gemini():
    """Mengkonfigurasi dan menginisialisasi model Gemini."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash') # Menggunakan Flash untuk kecepatan
        return model
    except Exception as e:
        print(f"Error konfigurasi Gemini: {e}")
        return None

def analyze_with_gemini(model, log_entries_str):
    """Mengirim log ke Gemini untuk analisis."""
    if not model:
        return "Analisis Gemini tidak tersedia (model gagal dimuat)."

    prompt = f"""
    Analisis log SSH berikut dari server saya. 
    Berikan ringkasan ancaman dalam satu paragraf singkat dan sarankan satu tindakan spesifik (misalnya, format perintah firewall/fail2ban).
    Target audiens adalah admin sistem yang sedang bepergian.

    Log:
    {log_entries_str}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error saat memanggil Gemini API: {e}")
        return f"Gagal menganalisis log. Serangan terdeteksi dari log berikut:\n{log_entries_str}"

def send_whatsapp_notification(message):
    """Mengirim pesan ke WhatsApp menggunakan Fonnte."""
    url = "https://api.fonnte.com/send"
    payload = {
        'target': YOUR_PHONE_NUMBER,
        'message': message,
    }
    headers = {
        'Authorization': FONNTE_API_TOKEN
    }
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status() # Cek jika ada HTTP error
        print(f"Notifikasi WhatsApp terkirim ke {YOUR_PHONE_NUMBER}.")
    except requests.exceptions.RequestException as e:
        print(f"Error mengirim notifikasi Fonnte: {e}")

# --- 3. FUNGSI UTAMA (MAIN) ---

def parse_log_time(timestamp_str):
    """Mengubah format waktu log (Nov 10 19:30:01) ke objek datetime."""
    # Menambahkan tahun saat ini karena log tidak menyertakan tahun
    log_time = datetime.strptime(timestamp_str, '%b %d %H:%M:%S')
    return log_time.replace(year=datetime.now().year)

def main():
    print(f"Memulai monitor SSH pada {datetime.now()}...")
    gemini_model = setup_gemini()
    
    time_threshold = datetime.now() - timedelta(minutes=TIME_WINDOW_MINUTES)
    
    # Dictionary untuk menghitung kegagalan per IP
    # dan menyimpan log yang relevan
    ip_failures = defaultdict(int)
    ip_log_entries = defaultdict(list)

    try:
        with open(LOG_FILE_PATH, 'r') as f:
            for line in f:
                match = LOG_PATTERN.search(line)
                
                if match:
                    timestamp_str, ip_address = match.groups()
                    log_time = parse_log_time(timestamp_str)
                    
                    # Hanya proses log dalam jendela waktu yang ditentukan
                    if log_time > time_threshold:
                        ip_failures[ip_address] += 1
                        ip_log_entries[ip_address].append(line.strip())

    except FileNotFoundError:
        print(f"Error: File log tidak ditemukan di {LOG_FILE_PATH}")
        return
    except PermissionError:
        print(f"Error: Tidak memiliki izin untuk membaca {LOG_FILE_PATH}.")
        print("Pastikan Jenkins memiliki izin baca.")
        return
    except Exception as e:
        print(f"Error saat membaca file log: {e}")
        return

    # --- 4. PEMROSESAN HASIL & PEMBERITAHUAN ---
    
    print(f"Pengecekan selesai. Menemukan {len(ip_failures)} IP dengan kegagalan.")
    
    alert_triggered = False
    for ip, count in ip_failures.items():
        if count >= FAILURE_THRESHOLD:
            alert_triggered = True
            print(f"AMBANG BATAS TERLAMPAUI! IP: {ip}, Percobaan: {count}")
            
            # Gabungkan semua log untuk IP ini menjadi satu string
            log_str = "\n".join(ip_log_entries[ip])
            
            # 1. Dapatkan Analisis Gemini
            print(f"Mendapatkan analisis dari Gemini untuk IP {ip}...")
            analysis_result = analyze_with_gemini(gemini_model, log_str)
            
            # 2. Siapkan Pesan WhatsApp
            header = f"🚨 PERINGATAN BRUTE FORCE SSH 🚨\n\n"
            details = f"IP Asal: {ip}\nJumlah Percobaan: {count}\nRentang Waktu: {TIME_WINDOW_MINUTES} menit terakhir\n\n"
            gemini_section = f"🤖 Analisis Gemini:\n{analysis_result}"
            
            final_message = header + details + gemini_section
            
            # 3. Kirim Notifikasi
            send_whatsapp_notification(final_message)

    if not alert_triggered:
        print("Sistem aman, tidak perlu khawatir. Tidak ada IP yang melampaui ambang batas.")

if __name__ == "__main__":
    main()