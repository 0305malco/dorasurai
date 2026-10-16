import os
import requests

# 金庫から鍵を取り出す
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

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
                "select": {"name": area}
            },
            "ジモティーリンク": {
                "url": link
            }
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code

# 起動テスト（本番運用の第一歩）
if __name__ == "__main__":
    status = add_to_notion(
        title="【完全自動テスト】大阪・昭和レトロ古書＆奈良訳あり平屋 巡回ロボ起動", 
        price="0円", 
        area="大阪・古本", 
        link="https://jmty.jp"
    )
    if status == 200:
        print("泥浚い成功！ダッシュボードに届いたで！")
    else:
        print(f"あかん、失敗や... エラー: {status}")
