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

# 正しいジモティーのURL（大阪の本・雑誌、奈良の不動産）
TARGET_URLS = [
    {"url": "https://jmty.jp/osaka/sale-boo", "area": "大阪・古本"},
    {"url": "https://jmty.jp/nara/est", "area": "奈良・不動産"}
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
            print(f"取得失敗: {target['url']} (Status: {res.status_code})")
            continue

        soup = BeautifulSoup(res.text, "html.parser")
        
        # 記事リンク（aタグ）を広めに検索
        articles = soup.select("a[href*='/articles/']")
        found_count = 0

        for a_tag in articles:
            link = a_tag.get("href", "")
            if not link.startswith("http"):
                link = "https://jmty.jp" + link
            
            parent = a_tag.find_parent("li") or a_tag.find_parent("div")
            if not parent:
                continue

            title = a_tag.text.strip()
            if not title:
                title_elem = parent.select_one(".p-item__title, .p-article-pl-title, h2")
                title = title_elem.text.strip() if title_elem else ""

            if not title or len(title) < 2:
                continue

            price_elem = parent.select_one(".p-item__price, .p-article-pl-price, .price")
            price = price_elem.text.strip() if price_elem else "価格記載なし"

            if link not in existing_links:
                add_to_notion(title, price, target["area"], link)
                existing_links.add(link)
                found_count += 1
                print(f"【新着発見】{title} ({price})")

        print(f"エリア[{target['area']}]の巡回完了: {found_count}件追加")

if __name__ == "__main__":
    scrape_jmty()
