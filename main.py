import time
import requests
import os
import difflib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# --- SENİN BİLGİLERİN ---
OKUL_NO = "b220100041"
SIFRE = "Alperharbidelirdi54?"
TELEGRAM_TOKEN = "7920565399:AAHIKSzYVzhpL-_1BJKMYDfdd5nUWlEHEtw"
CHAT_ID = "5018466961"
HEDEF_LINK = "https://obs.sabis.sakarya.edu.tr/Ders"
KAYIT_DOSYASI = "sabis_hafiza.txt"

# Bu kelimeleri içeren satırları direkt çöpe at
YASAKLI_KELIMELER = [
    "ALPER MERCAN", "Oran", "Çalışma Tipi", "Not", "Etki", 
    "Tarih", "Açıklama", "Genel Duyuru", "Seçilen Dersler", 
    "Ders Programı", "Sınav Takvimi", "Transkript", "Enstitü",
    "Öğrenci Bilgi Sistemi", "SABİS", "Sakarya Üniversitesi",
    "Öğretim", "Grubu", "SAU", "MÜHENDİSLİK"
]

def bildirim_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mesaj}
        requests.post(url, data=data)
    except: pass

def veriyi_guzellestir(ham_metin):
    satirlar = ham_metin.splitlines()
    temiz_liste = []
    son_ders = None # Başlangıçta ders yok

    for satir in satirlar:
        satir = satir.strip()
        if len(satir) < 2: continue
        
        # Yasaklı kelime varsa geç
        if any(yasak in satir for yasak in YASAKLI_KELIMELER):
            continue

        # --- BASİT VE NET MANTIK ---
        
        # 1. NOT SATIRI MI? (Rakamla başlıyorsa kesin nottur)
        # Örnek: "50 Ara Sınav 100"
        if satir[0].isdigit():
            # Eğer henüz bir ders bulamadıysak bu çöp veridir (en tepedeki sayılar vs), geç.
            if son_ders is None:
                continue
                
            # Baştaki oranı (50'yi) temizleyelim
            parcalar = satir.split()
            if len(parcalar) > 1:
                not_detayi = " ".join(parcalar[1:]) # "Ara Sınav 100"
                
                yeni_format = f"📘 {son_ders}\n   ✅ {not_detayi}"
                
                # Listede aynısı yoksa ekle
                if yeni_format not in temiz_liste:
                    temiz_liste.append(yeni_format)
        
        # 2. DERS ADI MI? (Büyük harfliyse ve rakamla başlamıyorsa derstir)
        elif satir.isupper() and len(satir) > 4:
            son_ders = satir

    return "\n".join(temiz_liste)

def farklari_bul(eski, yeni):
    # Sadece 📘 ile başlayan satırları kıyasla
    diff = difflib.ndiff(eski.splitlines(), yeni.splitlines())
    return [l[2:].strip() for l in diff if l.startswith('+ ') and "📘" in l]

def robotu_calistir():
    print("🚀 GitHub Robotu Çalışıyor...")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # GİRİŞ İŞLEMLERİ
        driver.get("https://sabis.sakarya.edu.tr")
        time.sleep(2)
        driver.find_element(By.ID, "UserName").send_keys(OKUL_NO)
        driver.find_element(By.ID, "Password").send_keys(SIFRE)
        driver.find_element(By.ID, "btnLogin").click()
        time.sleep(3)
        
        driver.get(HEDEF_LINK)
        time.sleep(3)

        if "Login" in driver.current_url or "Giriş" in driver.title:
            try:
                driver.get("https://sabis.sakarya.edu.tr")
                time.sleep(2)
                driver.find_element(By.XPATH, "//*[contains(text(), 'ÖĞRENCİ BİLGİ SİSTEMİ')]").click()
                time.sleep(5)
            except: pass

            try:
                kullanici = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                if not kullanici: kullanici = driver.find_elements(By.CSS_SELECTOR, "input[type='email']")
                if kullanici:
                    kullanici[0].clear()
                    kullanici[0].send_keys(OKUL_NO)
                    sifre = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
                    if sifre:
                        sifre[0].clear()
                        sifre[0].send_keys(SIFRE)
                        time.sleep(1)
                        sifre[0].send_keys(Keys.ENTER)
                        try:
                            driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
                        except: pass
            except: pass
            
            time.sleep(5)
            driver.get(HEDEF_LINK)
        
        time.sleep(5)
        
        # VERİYİ ÇEK VE İŞLE
        ham_veri = driver.find_element(By.TAG_NAME, "body").text
        yeni_veri = veriyi_guzellestir(ham_veri)
        
        if not os.path.exists(KAYIT_DOSYASI):
            with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(yeni_veri)
            # İlk seferde tüm notları görmek için bunu açtım:
            bildirim_gonder("✅ Sistem Hazır! İşte mevcut notların:\n\n" + yeni_veri)
        else:
            with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f: eski_veri = f.read()
            
            if yeni_veri != eski_veri:
                degisiklikler = farklari_bul(eski_veri, yeni_veri)
                if degisiklikler:
                    mesaj = "📢 YENİ NOT GİRİLDİ!\n\n" + "\n\n".join(degisiklikler) + "\n\n🔗 obs.sabis.sakarya.edu.tr/Ders"
                    bildirim_gonder(mesaj)
                    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(yeni_veri)
            else:
                print("Değişiklik yok.")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    robotu_calistir()
