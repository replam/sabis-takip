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

def bildirim_gonder(mesaj):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": mesaj}
        requests.post(url, data=data)
    except: pass

def veriyi_guzellestir(ham_metin):
    """
    Sayfadaki satırları analiz eder.
    Eğer bir satır NOT satırı ise (Sayı ile başlıyorsa), 
    onun başına en son okuduğu DERS ismini ekler.
    """
    satirlar = ham_metin.splitlines()
    islenmis_liste = []
    son_baslik = "Genel Duyuru" # İlk başta varsayılan başlık

    for satir in satirlar:
        satir = satir.strip()
        if not satir: continue

        # KRİTİK NOKTA: Not satırlarını tespit etme mantığı
        # Senin attığın resimde not satırı "50 Ara Sınav" diye başlıyor (Rakamla).
        # Ders isimleri ise harfle başlar.
        
        # Eğer satır bir RAKAM ile başlıyorsa, bu bir nottur.
        if satir[0].isdigit() and len(satir) < 100:
            # Bu satırı, hafızadaki son başlıkla birleştir
            yeni_satir = f"👉 {son_baslik} \n   ↳ {satir}"
            islenmis_liste.append(yeni_satir)
        else:
            # Rakamla başlamıyorsa bu bir ders ismidir (veya menü yazısıdır)
            # Bunu hafızaya alalım
            if len(satir) > 3: # Çok kısa (1-2 harflik) şeyleri ders sanmasın
                son_baslik = satir
            # Bu satırı olduğu gibi de listeye ekleyelim ki sayfa yapısı bozulmasın
            islenmis_liste.append(satir)

    return "\n".join(islenmis_liste)

def farklari_bul(eski, yeni):
    diff = difflib.ndiff(eski.splitlines(), yeni.splitlines())
    # Sadece + ile başlayan (yeni eklenen) satırları al
    # Ama sadece bizim "👉" işareti koyduklarımızı (yani notları) alırsak daha temiz olur
    return [l[2:].strip() for l in diff if l.startswith('+ ') and "👉" in l]

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
        
        # 2. OBS GİRİŞ (Zorba Mod)
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
        
        # 3. VERİ İŞLEME (EKLENEN KISIM)
        ham_veri = driver.find_element(By.TAG_NAME, "body").text
        
        # Ham veriyi alıp "Ders Adı -> Not" formatına çeviriyoruz
        islenmis_veri = veriyi_guzellestir(ham_veri)
        
        if not os.path.exists(KAYIT_DOSYASI):
            with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(islenmis_veri)
            # İlk seferde mesaj atmasın, sessizce kaydetsin (veya istersen atabilir)
            print("İlk kayıt alındı.")
        else:
            with open(KAYIT_DOSYASI, "r", encoding="utf-8") as f: eski_veri = f.read()
            
            if islenmis_veri != eski_veri:
                degisiklikler = farklari_bul(eski_veri, islenmis_veri)
                if degisiklikler:
                    # Mesajı hazırla
                    mesaj = "📢 YENİ NOT GİRİLDİ!\n\n" + "\n\n".join(degisiklikler) + "\n\n🔗 obs.sabis.sakarya.edu.tr/Ders"
                    bildirim_gonder(mesaj)
                    
                    # Dosyayı güncelle
                    with open(KAYIT_DOSYASI, "w", encoding="utf-8") as f: f.write(islenmis_veri)
            else:
                print("Değişiklik yok.")

    except Exception as e:
        print(f"Hata: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    robotu_calistir()
