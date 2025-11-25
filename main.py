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

# YASAKLI KELİMELER (Bunları görünce direkt atlasın)
YASAKLI_KELIMELER = [
    "ALPER MERCAN", "Oran", "Çalışma Tipi", "Not", "Etki", 
    "Tarih", "Açıklama", "Genel Duyuru", "Seçilen Dersler", 
    "Ders Programı", "Sınav Takvimi", "Transkript", "Enstitü",
    "Öğrenci Bilgi Sistemi", "SABİS", "Sakarya Üniversitesi",
    "Öğretim", "Grubu", "SAU", "MÜHENDİSLİK FAKÜLTESİ", 
    "Dönem", "Kredi", "AKTS"
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
    son_ders = "DERS BULUNAMADI"
    
    # Not olabilecek kelimeler
    anahtar_kelimeler = ["Sınav", "Vize", "Final", "Ödev", "Proje", "Quiz", "Bütünleme"]

    for satir in satirlar:
        satir = satir.strip()
        if len(satir) < 2: continue
        
        # Yasaklı kelime varsa geç
        if any(yasak in satir for yasak in YASAKLI_KELIMELER):
            continue

        # --- YENİ ANALİZ MANTIĞI ---
        
        # 1. DERS ADI BULMA (Büyük harf ve uzunluk kontrolü)
        # İçinde rakam olmayan, uzun ve büyük harfli satırlar derstir.
        if satir.isupper() and len(satir) > 5 and not any(c.isdigit() for c in satir):
            son_ders = satir
            continue # Ders adını bulduk, sıradaki satıra geç

        # 2. NOT SATIRI BULMA
        # İçinde anahtar kelime geçiyorsa (Sınav, Ödev vs.) VEYA sonunda rakam varsa al.
        kelime_var = any(kelime in satir for kelime in anahtar_kelimeler)
        rakam_var = any(c.isdigit() for c in satir)
        
        if (kelime_var or rakam_var) and len(satir) < 80:
            # Satırı temizle (Baştaki oran sayısını silmeye çalışalım)
            parcalar = satir.split()
            
            # Eğer ilk kelime bir sayıysa (50, 40 gibi oranlar), onu at.
            if len(parcalar) > 1 and parcalar[0].isdigit():
                temiz_satir = " ".join(parcalar[1:])
            else:
                temiz_satir = satir
                
            yeni_format = f"📘 {son_ders}\n   ✅ {temiz_satir}"
            
            # Aynı şeyi tekrar eklememek için kontrol
            if yeni_format not in temiz_liste:
                temiz_liste.append(yeni_format)

    return "\n".join(temiz_liste)

def farklari_bul(eski, yeni):
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
        # 1. GİRİŞ
        driver.get("https://sabis.sakarya.edu.tr")
        time.sleep(2)
        driver.find_element(By.ID, "UserName").send_keys(OKUL_NO)
        driver.find_element(By.ID, "Password").send_keys(SIFRE)
        driver.find_element(By.ID, "btnLogin").click()
        time.sleep(3)
        
        # 2. OBS GİRİŞ
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
        
        # 3. VERİ ÇEKME
        ham_veri = driver.find_element(By.TAG_NAME, "body").text
        
        # VERİYİ GÜZELLEŞTİR
        yeni_veri = veriyi_guzellestir(ham_veri)
        
        if not os.path.exists(KAYIT_DOSYASI):
            with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(yeni_veri)
            print("İlk kayıt alındı.")
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
