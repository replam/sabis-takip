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

# --- SENİN BİLGİLERİN (GÖMÜLÜ) ---
OKUL_NO = "b220100041"
SIFRE = "Alperharbidelirdi54?"
TELEGRAM_TOKEN = "7920565399:AAHIKSzYVzhpL-_1BJKMYDfdd5nUWlEHEtw"
CHAT_ID = "5018466961"
HEDEF_LINK = "https://obs.sabis.sakarya.edu.tr/Ders"
KAYIT_DOSYASI = "sabis_hafiza.txt"

def bildirim_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mesaj}
        requests.post(url, data=data)
    except: pass

def farklari_bul(eski, yeni):
    # Sadece yeni eklenen satırları (+ ile başlayanları) bul
    diff = difflib.ndiff(eski.splitlines(), yeni.splitlines())
    return [l[2:].strip() for l in diff if l.startswith('+ ') and len(l) > 2]

def robotu_calistir():
    print("🚀 GitHub Robotu Çalışıyor...")
    
    # GitHub ayarları (Ekran yok, sessiz mod)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # 1. GİRİŞ
        driver.get("https://sabis.sakarya.edu.tr")
        time.sleep(2)
        driver.find_element(By.ID, "UserName").send_keys(OKUL_NO)
        driver.find_element(By.ID, "Password").send_keys(SIFRE)
        driver.find_element(By.ID, "btnLogin").click()
        time.sleep(3)
        
        # 2. OBS VE ÇİFT GİRİŞ KONTROLÜ (Zorba Mod)
        driver.get(HEDEF_LINK)
        time.sleep(3)

        # Eğer giriş sayfasına attıysa (Login başlığı varsa)
        if "Login" in driver.current_url or "Giriş" in driver.title:
            print("İkinci giriş gerekiyor...")
            try:
                # Bazen direkt kırmızı butona basmak gerekir
                driver.get("https://sabis.sakarya.edu.tr")
                time.sleep(2)
                driver.find_element(By.XPATH, "//*[contains(text(), 'ÖĞRENCİ BİLGİ SİSTEMİ')]").click()
                time.sleep(5)
            except: pass

            # İkinci şifreyi gir (Identity Server)
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
                        # Garanti olsun diye butona da tıkla
                        try:
                            driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, "button[type='submit']"))
                        except: pass
            except: pass
            
            time.sleep(5)
            driver.get(HEDEF_LINK) # Tekrar ders sayfasına git
        
        time.sleep(5)
        
        # 3. VERİ ÇEKME VE KIYASLAMA
        yeni_veri = driver.find_element(By.TAG_NAME, "body").text
        
        # Dosya yoksa oluştur (İlk çalışma)
        if not os.path.exists(KAYIT_DOSYASI):
            with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(yeni_veri)
            bildirim_gonder("✅ GitHub Sistem Başlatıldı! İlk kayıt alındı. (20 dk modu)")
        else:
            with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f: eski_veri = f.read()
            
            if yeni_veri != eski_veri:
                degisiklikler = farklari_bul(eski_veri, yeni_veri)
                if degisiklikler:
                    mesaj = "📢 YENİ NOT GİRİLDİ!\n\n" + "\n".join(degisiklikler) + "\n\n🔗 obs.sabis.sakarya.edu.tr/Ders"
                    bildirim_gonder(mesaj)
                    # Dosyayı güncelle
                    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(yeni_veri)
            else:
                print("Değişiklik yok.")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":

    robotu_calistir()
    
    
    
