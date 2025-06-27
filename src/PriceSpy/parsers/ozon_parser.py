#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import random
import json
import urllib.parse

import undetected_chromedriver as uc
from selenium.webdriver.common.by           import By
from selenium.webdriver.common.keys         import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui          import WebDriverWait
from selenium.webdriver.support             import expected_conditions as EC
from selenium.common.exceptions             import TimeoutException

# Максимальное число ссылок на товар за один поисковый запрос
MAX_PER_NAME = 3
# Прокси (None — без прокси)
PROXY = None

def human_delay(a: float = 0.3, b: float = 1.2) -> None:
    """Небольшая рандомная задержка."""
    time.sleep(random.uniform(a, b))

def human_typing(el, text: str) -> None:
    """Эмуляция человекоподобной печати."""
    for ch in text:
        el.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.2))

def init_driver() -> uc.Chrome:
    """
    Запускает undetected-chromedriver в headless режиме.
    undetected_chromedriver сам подтянет подходящий ChromeDriver.
    """
    opts = uc.ChromeOptions()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--window-size=1920,1080")

    # рандомный юзер-агент
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/14.1 Safari/605.1.15",
    ]
    opts.add_argument(f"user-agent={random.choice(uas)}")

    if PROXY:
        opts.add_argument(f"--proxy-server={PROXY}")

    # бинарник Chrome в контейнере (указываем через ENV CHROME_BIN)
    bin_path = os.getenv("CHROME_BIN")
    if bin_path:
        opts.binary_location = bin_path

    driver = uc.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    return driver

def search_and_get_links(driver: uc.Chrome, query: str) -> list[str]:
    """
    Переходим сразу на страницу поиска Ozon:
      https://www.ozon.ru/search/?text=<query>
    Ждём появления любых ссылок на товары и собираем первые MAX_PER_NAME уникальных URL.
    """
    encoded = urllib.parse.quote_plus(query)
    driver.get(f"https://www.ozon.ru/search/?text={encoded}")

    # ждём, пока появится хотя бы один товарный линк
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/product/']"))
        )
    except TimeoutException:
        # если за 20 сукнд не загрузилось — сохраним HTML и упадём
        with open("ozon_search_failed.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        raise RuntimeError(
            "Поиск на Ozon.ru не вернул результатов за 20 с. — "
            "HTML сохранён в ozon_search_failed.html"
        )

    # множественные прокрутки для подгрузки lazy-load карточек
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, window.innerHeight*0.7);")
        human_delay(0.5, 1.0)

    elems = driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
    links: list[str] = []
    for a in elems:
        href = a.get_attribute("href") or ""
        clean = href.split("?")[0]
        if "/product/" in clean and clean not in links:
            links.append(clean)
        if len(links) >= MAX_PER_NAME:
            break

    if not links:
        raise RuntimeError(f"По запросу «{query}» не найдено ни одной ссылки на товары")

    return links

def parse_product(driver: uc.Chrome, url: str) -> tuple[
    str|None, str|None, str|None, str|None, float|None, int|None, str|None
]:
    """
    Открывает карточку товара по URL и парсит JSON-LD из
    <script type="application/ld+json">, возвращая:
      sku, name, description, price_str, rating, review_count, image_url
    """
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "script[type='application/ld+json']"))
    )
    human_delay(1, 2)

    # пара прокруток для загрузки всех данных
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, window.innerHeight*0.5);")
        human_delay(0.5, 1.0)

    scripts = driver.find_elements(By.CSS_SELECTOR, "script[type='application/ld+json']")
    info = {}
    for s in scripts:
        try:
            data = json.loads(s.get_attribute("innerHTML") or "")
        except:
            continue

        # находим объект с "@type": "Product"
        prod = None
        if isinstance(data, list):
            prod = next((x for x in data if x.get("@type") == "Product"), None)
        elif data.get("@type") == "Product":
            prod = data

        if prod:
            info = prod
            break

    sku     = info.get("sku")
    name    = info.get("name")
    desc    = info.get("description")
    img     = info.get("image")
    if isinstance(img, list):
        img = img[0]

    offers = info.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0]
    price      = offers.get("price")
    currency   = offers.get("priceCurrency")
    price_str  = f"{price} {currency}".strip() if (price or currency) else None

    agg          = info.get("aggregateRating") or {}
    rating       = agg.get("ratingValue") or info.get("ratingValue")
    review_count = agg.get("reviewCount") or info.get("reviewCount")

    return sku, name, desc, price_str, rating, review_count, img
