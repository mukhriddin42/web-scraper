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

@app.get("/")
def home():
    return {"message": "Welcome to the Web Scraper API"}

@app.post("/scrape")
def scrape_website():
    return {"message": "Scraping ishladi!"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

app.mount("/static", StaticFiles(directory="static"), name="static")









# Templates sozlamalari
templates = Jinja2Templates(directory="templates")

# UI sahifasini xizmat qilish
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Scraping endpoint
@app.post("/scrape")
def scrape_website(request: dict):
    url = request.get("url")

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Saytga ulanishda xatolik: {str(e)}")

    soup = BeautifulSoup(response.text, "html.parser")
    headlines = soup.find_all("h1")
    paragraphs = soup.find_all("p")

    data = []
    for i in range(min(len(headlines), len(paragraphs))):
        data.append([headlines[i].get_text(strip=True), paragraphs[i].get_text(strip=True)])

    file_path = "data/scraped_data.csv"
    os.makedirs("data", exist_ok=True)

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Sarlavha", "Matn"])
        writer.writerows(data)

    return {"message": "Ma'lumot muvaffaqiyatli yig‘ildi!", "file_path": file_path}

# CSV yuklab olish
@app.get("/download")
def download_csv():
    file_path = "data/scraped_data.csv"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="CSV fayl topilmadi")
    return FileResponse(file_path, filename="scraped_data.csv", media_type="text/csv")



