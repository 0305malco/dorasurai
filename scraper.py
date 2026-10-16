import os
import requests
from bs4 import BeautifulSoup

NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# 巡回ターゲット（大阪の古本・レトロ、奈良の不動産・訳ありなど）
TARGET_URLS = [
    {"url": "https://jmty.jp/osaka/sale-book/g-all", "area": "大阪・古本"},
    {"url": "https://jmty.jp/nara/est-all/g-all", "area": "奈良・不動産"}
]

# Notionにすでに登録済みのリンク一覧を取得（二重登録を防ぐため）
def get_existing_links():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    existing_links = set()
    has_more = True
    start_cursor = None

    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
        
        res = requests.post(url, headers=headers, json=payload)
        if res.status_code == 200:
            data = res.json()
            for page in data.get("results", []):
                link_prop = page["properties"].get("ジモティーリンク", {}).get("url")
                if link_prop:
                    existing_links.add(link_prop)
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        else:
            break
    return existing_links

# Notionへデータを叩き込む関数
def add_to_notion(title, price, area, link):
    url = "https://api.notion.com/v1/pages"
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "商品名・件名": {
                "title": [{"text": {"content": title}}]
            },
            "価格": {
                "rich_text": [{"text": {"content": price}}]
            },
            "エリア": {
                "multi_select": [{"name": area}]
            },
            "ジモティーリンク": {
                "url": link
            }
        }
    }
    requests.post(url, headers=headers, json=data)

# ジモティーを泥浚いするメイン処理
def scrape_jmty():
    existing_links = get_existing_links()
    print(f"取得済みリンク数: {len(existing_links)}")

    ua_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    for target in TARGET_URLS:
        res = requests.get(target["url"], headers=ua_headers)
        if res.status_code != 200:
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.find_all("li", class_="p-item")

        for item in items:
            title_elem = item.find("div", class_="p-item__title")
            price_elem = item.find("div", class_="p-item__price")
            link_elem = title_elem.find("a") if title_elem else None

            if title_elem and link_elem:
                title = title_elem.text.strip()
                link = link_elem.get("href", "")
                price = price_elem.text.strip() if price_elem else "価格記載なし"

                if link and link not in existing_links:
                    add_to_notion(title, price, target["area"], link)
                    existing_links.add(link)
                    print(f"【新着発見】{title} ({price})")

if __name__ == "__main__":
    scrape_jmty()
