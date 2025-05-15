from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from bs4 import BeautifulSoup
import requests
import uvicorn
import csv
import os

app = FastAPI()

# Statik fayllar va HTML shablonlar
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Bosh sahifa
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Web scraping va CSV saqlash
@app.post("/scrape")
def scrape_website(request: dict):
    url = request.get("url")

    # Saytga ulanish va xatoliklarni tekshirish (BU QISM O'ZGARMADI)
    try:
        response = requests.get(url)
        response.raise_for_status()  # Xatolik status kodlarini tekshiradi (4xx, 5xx)
    except requests.exceptions.RequestException as e:
        # Ulanish yoki so'rov xatoliklari
        raise HTTPException(status_code=400, detail=f"Saytga ulanishda yoki ma'lumot olishda xatolik: {str(e)}")
    except Exception as e:
        # Boshqa kutilmagan xatoliklar
        raise HTTPException(status_code=500, detail=f"Kutilmagan xatolik yuz berdi: {str(e)}")

    # HTML sahifani BeautifulSoup yordamida tahlil qilish (BU QISM O'ZGARMADI)
    soup = BeautifulSoup(response.text, "html.parser")

    # --- BU QISM O'ZGARTIRILADI: Advice.uz savol-javoblarini ajratib olish ---
    data_to_save = [] # Saqlanadigan ma'lumotlar uchun bo'sh ro'yxat

    # Savol-javoblar ro'yxatini o'z ichiga olgan asosiy konteynerni topamiz
    qa_list_container = soup.find("div", class_="document-requests-list")

    if qa_list_container:
        # Agar konteyner topilsa, uning ichidagi har bir savol-javob elementini topamiz
        qa_items = qa_list_container.find_all("div", class_="document-request-item")

        if qa_items:
            # Har bir savol-javob elementini aylanib chiqamiz
            for item in qa_items:
                # Savol elementini topamiz
                question_element = item.find("a", class_="document-request-item__title")
                # Javob elementini topamiz
                answer_element = item.find("div", class_="document-request-item__body")

                # Matn kontentini olamiz va bo'shliqlarni tozalaymiz
                question_text = question_element.get_text(strip=True) if question_element else "Savol topilmadi"
                # Javob matni ko'pincha bir nechta blokdan iborat bo'lishi mumkin,
                # shuning uchun get_text(separator='\n') qulayroq
                answer_text = answer_element.get_text(strip=True, separator='\n') if answer_element else "Javob topilmadi"

                # Ajratib olingan savol va javobni ro'yxatga qo'shamiz
                data_to_save.append([question_text, answer_text])
        else:
            # Agar konteyner topilsa, lekin ichida savol-javob elementlari bo'lmasa
            data_to_save.append(["Savol-javoblar topilmadi", ""])
    else:
        # Agar asosiy savol-javoblar konteyneri topilmasa
        data_to_save.append(["Savol-javob qismi topilmadi", ""])
    # --- O'ZGARTIRILGAN QISM TUGADI ---


    # CSV faylga saqlash (FAYL YO'LI VA PAPKA YARATISH O'ZGARMADI)
    file_path = "data/scraped_data.csv"
    os.makedirs("data", exist_ok=True)

    # CSV faylga yozish
    # 'w' rejimida ochamiz, shunda har safar yangi ma'lumot yoziladi
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # CSV ustun nomlarini o'zgartiramiz
        writer.writerow(["Savol", "Javob"])
        # Ajratib olingan ma'lumotlarni yozamiz
        writer.writerows(data_to_save)

    # Foydalanuvchiga muvaffaqiyatli bajarilganligi haqida xabar berish (O'ZGARMADI)
    # Lekin xabarni biroz aniqlashtirish mumkin
    if data_to_save and (data_to_save[0][0] not in ["Savol-javob qismi topilmadi", "Savol-javoblar topilmadi"]):
         return {"message": f"Ma'lumot muvaffaqiyatli yig‘ildi ({len(data_to_save)} ta savol-javob) va CSV faylga saqlandi!", "file_path": file_path}
    else:
         return {"message": data_to_save[0][0], "file_path": file_path} # Agar topilmasa, xabarni qaytaramiz

# CSV faylni yuklab olish
@app.get("/download")
def download_csv():
    file_path = "data/scraped_data.csv"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV fayl topilmadi")
    return FileResponse(file_path, filename="scraped_data.csv", media_type="text/csv")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
