"""
SUUMO 中古マンション 詳細ページの解析。

SUUMOの物件詳細ページ（例: https://suumo.jp/ms/chuko/.../nc_XXXXXXXXX/）は
`dt`/`dd` の表（dottable）構造でサーバーレンダリングされており、
ラベル名（価格 / 所在地 / 専有面積 / 間取り / 築年月 / 沿線・駅 …）を手がかりに
ラベルベースで値を取り出す。クラス名に依存しないので markup 変更に比較的強い。

【重要・規約に関する注意】
SUUMOの自動アクセス／スクレイピングは同サイトの利用規約に抵触する可能性がある。
本番運用ではSUUMO（リクルート）との許諾、もしくは公式提供データの利用を検討すること。
本モジュールは:
  - 低頻度アクセス前提（CACHEや手動入力フォールバックと併用）
  - 礼儀的なUser-Agentを送出
  - 取得失敗時は PropertyParseError を投げ、呼び出し側で手入力に切り替えられる
ように作ってある。解析セレクタは差し替え可能。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (compatible; ISOGE-clone/1.0; +contact@example.com) "
    "appraisal-prototype"
)
TIMEOUT = 20

SUUMO_HOST_RE = re.compile(r"(^|\.)suumo\.jp$", re.I)


class PropertyParseError(RuntimeError):
    pass


@dataclass
class Property:
    name: str                      # 物件名
    price_yen: Optional[int]       # 売出価格（円）
    address: str                   # 所在地
    area_m2: Optional[float]       # 専有面積（㎡）
    floor_plan: str                # 間取り
    built_year: Optional[int]      # 築年（西暦）
    built_month: Optional[int]
    floor: Optional[int]           # 所在階
    station: str                   # 沿線・駅
    walk_min: Optional[int]        # 駅徒歩（分）
    structure: str                 # 構造・階建
    url: str

    @property
    def age(self) -> Optional[int]:
        if not self.built_year:
            return None
        return max(0, datetime.now().year - self.built_year)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["age"] = self.age
        return d


# --------------------------------------------------------------------------- #
# URL バリデーション
# --------------------------------------------------------------------------- #

def is_suumo_url(text: str) -> Optional[str]:
    """テキストからSUUMOのURLを1つ抽出して返す（無ければNone）。"""
    m = re.search(r"https?://[^\s]+", text or "")
    if not m:
        return None
    url = m.group().rstrip("　 、。)）」』>")
    from urllib.parse import urlparse
    host = urlparse(url).netloc.split(":")[0]
    if SUUMO_HOST_RE.search(host):
        return url
    return None


# --------------------------------------------------------------------------- #
# 取得
# --------------------------------------------------------------------------- #

def fetch_html(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise PropertyParseError(f"SUUMOページ取得に失敗しました（{resp.status_code}）")
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp.text


# --------------------------------------------------------------------------- #
# パース補助
# --------------------------------------------------------------------------- #

def _build_label_map(soup: BeautifulSoup) -> dict[str, str]:
    """dt/dd・th/td のラベル→値マップを作る。"""
    pairs: dict[str, str] = {}

    # dt/dd ペア
    for dt in soup.find_all(["dt", "th"]):
        label = dt.get_text(strip=True)
        if not label:
            continue
        sib = dt.find_next_sibling(["dd", "td"])
        if sib:
            val = sib.get_text(" ", strip=True)
            if label not in pairs and val:
                pairs[label] = val
    return pairs


def _find(pairs: dict[str, str], *keywords: str) -> Optional[str]:
    for label, val in pairs.items():
        if any(k in label for k in keywords):
            return val
    return None


def _parse_price_yen(s: Optional[str]) -> Optional[int]:
    """ "5,480万円" / "1億2,800万円" → 円 """
    if not s:
        return None
    s = s.replace(",", "").replace(" ", "")
    total = 0
    m_oku = re.search(r"(\d+(?:\.\d+)?)億", s)
    if m_oku:
        total += int(float(m_oku.group(1)) * 1_0000_0000)
    m_man = re.search(r"(\d+(?:\.\d+)?)万", s)
    if m_man:
        total += int(float(m_man.group(1)) * 1_0000)
    if total:
        return total
    m = re.search(r"\d+", s)
    return int(m.group()) if m else None


def _parse_area(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|㎡|平米|m2|m²)", s, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def _parse_built(s: Optional[str]) -> tuple[Optional[int], Optional[int]]:
    """ "1998年3月" / "平成10年3月築" → (1998, 3) """
    if not s:
        return None, None
    year = None
    month = None
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        year = int(m.group())
    else:
        from reinfolib import _to_west_year  # 和暦対応を再利用
        year = _to_west_year(s)
    mm = re.search(r"年\s*(\d{1,2})\s*月", s)
    if mm:
        month = int(mm.group(1))
    return year, month


def _parse_floor(s: Optional[str]) -> Optional[int]:
    """ "12階/15階建" / "3階" → 12 """
    if not s:
        return None
    m = re.search(r"(\d+)\s*階", s)
    return int(m.group(1)) if m else None


def _parse_walk(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    m = re.search(r"歩\s*(\d+)\s*分", s) or re.search(r"(\d+)\s*分", s)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------- #
# メイン
# --------------------------------------------------------------------------- #

def parse_property(html: str, url: str = "") -> Property:
    soup = BeautifulSoup(html, "html.parser")
    pairs = _build_label_map(soup)

    # 物件名: og:title or h1
    name = ""
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        name = og["content"].strip()
    if not name:
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else "物件"
    name = re.sub(r"[｜|].*$", "", name).strip()

    price = _parse_price_yen(_find(pairs, "価格", "販売価格"))
    address = _find(pairs, "所在地", "住所") or ""
    area = _parse_area(_find(pairs, "専有面積", "面積"))
    floor_plan = _find(pairs, "間取り") or ""
    built_year, built_month = _parse_built(_find(pairs, "築年月", "完成", "竣工", "建築年"))
    floor = _parse_floor(_find(pairs, "所在階", "階数", "向き/階"))
    station_raw = _find(pairs, "沿線・駅", "交通", "最寄") or ""
    structure = _find(pairs, "構造", "建物構造") or ""

    prop = Property(
        name=name or "物件",
        price_yen=price,
        address=address,
        area_m2=area,
        floor_plan=floor_plan,
        built_year=built_year,
        built_month=built_month,
        floor=floor,
        station=station_raw,
        walk_min=_parse_walk(station_raw),
        structure=structure,
        url=url,
    )

    if not (prop.price_yen and prop.area_m2 and prop.address):
        raise PropertyParseError(
            "物件情報の一部を取得できませんでした（価格・面積・所在地）。"
            "ページ構造が変わった可能性があります。手入力をご利用ください。"
        )
    return prop


def fetch_property(url: str) -> Property:
    return parse_property(fetch_html(url), url)
