#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import random
import csv
import json

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== НАСТРОЙКИ ==========
SEARCH_FILE    = "names.txt"   # вход: по одному названию товара в строке
OUTPUT_CSV     = "products.csv"
MAX_PER_NAME   = 3             # сколько первых результатов парсить для каждого запроса
PROXY          = None          # или "ip:port"
# ================================

def human_delay(a=0.3, b=1.2):
    time.sleep(random.uniform(a, b))

def init_driver():
    options = uc.ChromeOptions()
    # НЕ включаем headless
    # options.headless = True

    # прячем WebDriver fingerprint
    options.add_argument("--disable-blink-features=AutomationControlled")
    # рандомный User-Agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/14.1 Safari/605.1.15",
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")

    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")

    driver = uc.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

def human_typing(el, text):
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.25))

def search_and_get_links(driver, query):
    # 1) на главную
    driver.get("https://www.ozon.ru/")
    human_delay(1, 2)

    # 2) ждём поле поиска по атрибуту name="text"
    search_input = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[name='text']"))
    )
    ActionChains(driver).move_to_element(search_input).click().perform()
    human_typing(search_input, query)
    human_delay()
    search_input.submit()

    # 3) даём странице загрузиться
    human_delay(2, 4)

    # 4) скроллим вниз по чуть-чуть, чтобы подгрузить карточки
    for _ in range(4):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.75);")
        human_delay(0.5, 1.5)

    # 5) собираем первые ссылки с /product/
    elems = driver.find_elements(By.XPATH, "//a[contains(@href,'/product/')]")
    links = []
    for a in elems:
        href = a.get_attribute("href")
        if not href:
            continue
        clean = href.split("?")[0]
        if "/product/" in clean and clean not in links:
            links.append(clean)
        if len(links) >= MAX_PER_NAME:
            break

    if not links:
        raise RuntimeError("При поиске не нашлось ни одной ссылки /product/")
    return links

def parse_product(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "script[type='application/ld+json']"))
    )
    human_delay()

    # ещё пару скроллов, на всякий случай
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, window.innerHeight * 0.5);")
        human_delay(0.3, 0.8)

    scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
    info = {}
    for s in scripts:
        try:
            data = json.loads(s.get_attribute("innerHTML").strip())
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            prod = next((x for x in data if x.get("@type") == "Product"), None)
        elif data.get("@type") == "Product":
            prod = data
        else:
            prod = None

        if prod:
            info = prod
            break

    sku     = info.get("sku")
    name    = info.get("name")
    desc    = info.get("description")
    image   = info.get("image")
    if isinstance(image, list):
        image = image[0]

    offers = info.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0]
    price     = offers.get("price")
    currency  = offers.get("priceCurrency")
    price_str = f"{price} {currency}".strip() if price or currency else None

    agg        = info.get("aggregateRating") or {}
    rating       = agg.get("ratingValue") or info.get("ratingValue")
    review_count = agg.get("reviewCount") or info.get("reviewCount")

    return sku, name, desc, price_str, rating, review_count, image

def main():
    driver = init_driver()

    with open(SEARCH_FILE, encoding="utf-8") as fin, \
         open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as fout:

        writer = csv.writer(fout)
        writer.writerow([
            "Query","URL","SKU","Name","Description",
            "Price","Rating","ReviewCount","ImageURL"
        ])

        for line in fin:
            query = line.strip()
            if not query:
                continue

            try:
                links = search_and_get_links(driver, query)
                print(f"«{query}»: найдено {len(links)} ссылок")
            except Exception as e:
                print(f"Ошибка поиска «{query}»: {e.__class__.__name__}: {e}")
                continue

            for url in links:
                try:
                    sku, name, desc, price, rating, rc, img = parse_product(driver, url)
                    writer.writerow([query, url, sku, name, desc, price, rating, rc, img])
                    print(f"  → спарсил {url}")
                except Exception as e:
                    print(f"  ✗ не удалось спарсить {url}: {e}")
                human_delay(0.5, 1.2)

    driver.quit()
    print("Готово, результаты в", OUTPUT_CSV)

if __name__ == "__main__":
    main()