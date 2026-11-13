import json
import os
import re
import requests

# ===== 这里要修改！把你第一步记下的 ntfy 名字填进去 =====
NTFY_TOPIC = "Zhihu-alert-zwing-2026"
# =====================================================

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


# ===== 新增：把 API 链接转成能打开的网页链接 =====
def normalize_url(url):
    if not url:
        return ""
    # 知乎接口经常返回 api.zhihu.com/questions/123 这种，转成网页版
    if url.startswith("https://api.zhihu.com/questions/"):
        return url.replace(
            "https://api.zhihu.com/questions/",
            "https://www.zhihu.com/question/"
        )
    if url.startswith("https://api.zhihu.com/answers/"):
        return url.replace(
            "https://api.zhihu.com/answers/",
            "https://www.zhihu.com/answer/"
        )
    if url.startswith("https://api.zhihu.com/articles/"):
        return url.replace(
            "https://api.zhihu.com/articles/",
            "https://zhuanlan.zhihu.com/p/"
        )
    if url.startswith("http"):
        return url
    return ""


# ===== 新增：从 target 里拿链接，拿不到就用 id 拼 =====
def get_link(target):
    url = normalize_url(target.get("url", ""))
    if url:
        return url

    tid = target.get("id")
    ttype = target.get("type", "")
    if tid:
        if ttype == "question":
            return f"https://www.zhihu.com/question/{tid}"
        if ttype == "answer":
            return f"https://www.zhihu.com/answer/{tid}"
        if ttype == "article":
            return f"https://zhuanlan.zhihu.com/p/{tid}"
    return ""


def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36"
    }
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
        link = get_link(target)          # 新增：拿链接

        if heat >= 10000000 and title and title not in sent:
            push_url = f"https://ntfy.sh/{NTFY_TOPIC}"

            # 修改：消息正文里也放链接，方便复制
            message = f"标题：{title}\n热度：{detail_text}"
            if link:
                message += f"\n链接：{link}"

            # 新增：告诉 ntfy，点这条通知就打开 link
            push_headers = {}
            if link:
                push_headers["Click"] = link

            try:
                requests.post(
                    push_url,
                    data=message.encode("utf-8"),
                    headers=push_headers,
                    timeout=10
                )
                new_sent.add(title)
                print(f"已推送: {title} ({detail_text}) {link}")
            except Exception as e:
                print(f"推送失败: {e}")

    save_sent(new_sent)


if __name__ == "__main__":
    main()
