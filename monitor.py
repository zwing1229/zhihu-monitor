import json
import os
import re
import requests

NTFY_TOPIC = "Zhihu-alert-zwing-2026"

SENT_FILE = "sent_items.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent(sent_set):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump(list(sent_set), f, ensure_ascii=False, indent=2)

def parse_heat(text):
    match = re.search(r'([\d.]+)\s*万', text)
    if match:
        return float(match.group(1)) * 10000
    match = re.search(r'([\d.]+)', text)
    if match:
        return float(match.group(1))
    return 0

def main():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        resp = requests.get(
            "https://api.zhihu.com/topstory/hot-list?limit=30",
            headers=headers,
            timeout=30
        )
        data = resp.json().get("data", [])
    except Exception as e:
        print(f"获取数据失败: {e}")
        return

    sent = load_sent()
    new_sent = set(sent)

    for item in data:
        target = item.get("target", {})
        title = target.get("title", "")
        detail_text = item.get("detail_text", "")
        heat = parse_heat(detail_text)

        if heat >= 10000000 and title and title not in sent:
            push_url = f"https://ntfy.sh/{NTFY_TOPIC}"
            message = f"热度突破1000万！\n\n标题：{title}\n热度：{detail_text}"
            try:
                requests.post(push_url, data=message.encode("utf-8"), timeout=10)
                new_sent.add(title)
                print(f"已推送: {title} ({detail_text})")
            except Exception as e:
                print(f"推送失败: {e}")

    save_sent(new_sent)

if __name__ == "__main__":
    main()
