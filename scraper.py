import os
import re
from bs4 import BeautifulSoup
from googletrans import Translator
import pandas as pd
import time

SOURCE_DIR = "PobraneAmazon"
DIR_MAIN = "Opinie"
DIR_EN = os.path.join(DIR_MAIN, "EN")

BRAND = "Xiaomi"
MODEL = "Mi9"

MIN_WORDS = 0 

def setup_directories():
    if not os.path.exists(DIR_EN): os.makedirs(DIR_EN)

def get_sentiment(normalized_score):
    return 'P' if normalized_score > 0.5 else 'N'

def extract_score(text):
    if not text: return None
    match = re.search(r'(\d+[,.]\d+|\d+)', text)
    if match:
        return float(match.group(1).replace(',', '.'))
    return None

def process_amazon_strict_body():
    if not os.path.exists(SOURCE_DIR):
        print("Brak folderu źródłowego.")
        return

    setup_directories()
    translator = Translator()
    
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".html") or f.endswith(".htm")]
    # Sortowanie plików
    files.sort(key=lambda f: int(re.search(r'\d+', f).group()) if re.search(r'\d+', f) else 0)
    
    print(f"Znaleziono {len(files)} plików. Tryb: TYLKO TREŚĆ (bez nagłówków).")

    reviews_data = []
    count = 0

    for file_name in files:
        file_path = os.path.join(SOURCE_DIR, file_name)
        print(f"\n--- Plik: {file_name} ---")
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, 'html.parser')
            
            opinions = soup.find_all(attrs={"id": re.compile(r"customer_review")})
            if not opinions:
                opinions = soup.find_all('div', {'data-hook': 'review'})

            print(f"   Znaleziono {len(opinions)} kart opinii.")

            for i, opinion in enumerate(opinions, 1):
                
                body_elem = None
                raw_text = None

                body_elem = opinion.find(attrs={"data-hook": "review-body"})
                
                if body_elem:
                    original_span = body_elem.find('span', class_='cr-original-review-content')
                    if original_span:
                        for br in original_span.find_all(["br", "p"]): br.replace_with(" ")
                        raw_text = original_span.get_text(" ").strip()
                    else:
                        for br in body_elem.find_all(["br", "p"]): br.replace_with(" ")
                        raw_text = body_elem.get_text(" ").strip()
                
                else:
                    body_elem = opinion.find('span', class_='review-text-content')
                    if body_elem:
                        for br in body_elem.find_all(["br", "p"]): br.replace_with(" ")
                        raw_text = body_elem.get_text(" ").strip()

                if not raw_text:
                    continue
                
                raw_score = None
                star_elem = opinion.find('span', class_='a-icon-alt') 
                if not star_elem:
                     star_elem = opinion.find('i', class_=lambda x: x and 'a-icon-star' in x)
                
                if star_elem:
                    raw_score = extract_score(star_elem.get_text())

                if raw_score is None:
                    continue

                count += 1
                
                normalized_score = raw_score / 5.0
                formatted_score = "{:.3f}".format(normalized_score)
                sentiment = get_sentiment(normalized_score)

                try:
                    translation = translator.translate(raw_text, dest='en')
                    content_en = translation.text
                except:
                    content_en = raw_text

                print(f"   [+{count}] Treść: {content_en[:50]}...")

                filename = f"{BRAND}_{MODEL}_{formatted_score}_{sentiment}_{count}.txt"
                with open(os.path.join(DIR_EN, filename), "w", encoding="utf-8") as txt_file:
                    txt_file.write(content_en)
                
                clean_content_csv = content_en.replace('\n', ' ').replace('\r', '').replace(';', ',')
                reviews_data.append({
                    "filename": filename,
                    "score": formatted_score,
                    "sentiment": sentiment,
                    "content": clean_content_csv
                })

        except Exception as e:
            print(f"Błąd: {e}")

    if reviews_data:
        df = pd.DataFrame(reviews_data)
        csv_path = os.path.join(DIR_MAIN, "opinie_angielskie.csv")
        df.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
        print(f"\n--- SUKCES --- Zapisano {count} opinii.")
    else:
        print("Brak danych.")

if __name__ == "__main__":
    process_amazon_strict_body()