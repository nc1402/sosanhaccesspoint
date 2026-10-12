"""Đồng bộ danh sách AP từ draytek.com vào aps.json.
- Model mới trên web  -> thêm vào với needs_review=true (cần bổ sung thông số).
- Model biến mất      -> gắn discontinued=true (không xoá).
- Giữ nguyên mọi thông số đã nhập tay.
"""
import json, re, datetime, pathlib, requests
from bs4 import BeautifulSoup

LIST_URL = "https://draytek.com/products/access-points/"
FILE = pathlib.Path(__file__).resolve().parent.parent / "aps.json"
UA = {"User-Agent": "Mozilla/5.0 (aps-sosanh-updater)"}

def fetch_list():
    html = requests.get(LIST_URL, headers=UA, timeout=30).text
    found = {}
    for a in BeautifulSoup(html, "html.parser").select('a[href*="/products/vigorap-"]'):
        m = re.search(r"/products/(vigorap-[\w-]+)", a["href"])
        if not m: continue
        text = " ".join(a.get_text(" ").split())
        found[m.group(1)] = {"text": text, "url": "https://draytek.com/products/%s/" % m.group(1)}
    return found

def main():
    data = json.loads(FILE.read_text(encoding="utf-8"))
    web = fetch_list()
    if len(web) < 3:                      # trang đổi cấu trúc -> không ghi đè
        raise SystemExit("Chỉ đọc được %d model, bỏ qua." % len(web))
    known = {a["id"]: a for a in data["aps"]}
    changed = False
    for slug, w in web.items():
        base = re.sub(r"-series$", "", slug)
        if slug in known or base in known:
            a = known.get(slug) or known[base]
            if a.pop("discontinued", None): changed = True
            continue
        name = re.search(r"VigorAP \w+", w["text"])
        data["aps"].append({"id": slug, "name": name.group(0) if name else slug,
                            "needs_review": True, "url": w["url"], "note": w["text"]})
        changed = True; print("Model mới:", slug)
    for a in data["aps"]:
        if a["id"] not in web and a["id"] + "-series" not in web and not a.get("discontinued"):
            a["discontinued"] = True; changed = True; print("Không còn trên web:", a["id"])
    if changed:
        data["updated"] = datetime.date.today().isoformat()
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

main()
