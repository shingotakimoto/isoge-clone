from __future__ import annotations
# =====================================================================
# ISOGE! クローン — 単一ファイル版（Render等にそのまま載せられる）
#   SUUMO解析 → 国交省API照会 → 相場推定 → 割安判定 → Web/LINE出力
#   ※APIキー未設定なら自動でデモ動作（サンプル事例）
# =====================================================================
import base64, hashlib, hmac, json, os, math, re, statistics, datetime
from dataclasses import dataclass, field, asdict
from datetime import datetime as _dt
from functools import lru_cache
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup
from flask import Flask, abort, jsonify, request
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


_SAMPLE_COMPS_JSON = r'''[
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "38900000",
    "Area": "43",
    "UnitPrice": "904651",
    "FloorPlan": "3LDK",
    "BuildingYear": "2016年",
    "Structure": "ＳＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "3",
    "Period": "2025年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "牡丹",
    "TradePrice": "51400000",
    "Area": "52",
    "UnitPrice": "988461",
    "FloorPlan": "2LDK",
    "BuildingYear": "2018年",
    "Structure": "ＳＲＣ",
    "NearestStation": "辰巳",
    "TimeToNearestStation": "7",
    "Period": "2025年第2四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "74500000",
    "Area": "77",
    "UnitPrice": "967532",
    "FloorPlan": "4LDK",
    "BuildingYear": "2023年",
    "Structure": "ＳＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "4",
    "Period": "2023年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "深川",
    "TradePrice": "35900000",
    "Area": "46",
    "UnitPrice": "780434",
    "FloorPlan": "3LDK",
    "BuildingYear": "1999年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "4",
    "Period": "2025年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "35900000",
    "Area": "55",
    "UnitPrice": "652727",
    "FloorPlan": "3LDK",
    "BuildingYear": "1988年",
    "Structure": "ＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "13",
    "Period": "2025年第3四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東陽",
    "TradePrice": "75100000",
    "Area": "78",
    "UnitPrice": "962820",
    "FloorPlan": "3LDK",
    "BuildingYear": "2009年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "5",
    "Period": "2024年第1四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "枝川",
    "TradePrice": "44300000",
    "Area": "58",
    "UnitPrice": "763793",
    "FloorPlan": "3LDK",
    "BuildingYear": "2000年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "5",
    "Period": "2025年第1四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "新大橋",
    "TradePrice": "43500000",
    "Area": "59",
    "UnitPrice": "737288",
    "FloorPlan": "4LDK",
    "BuildingYear": "1994年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "3",
    "Period": "2025年第2四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "深川",
    "TradePrice": "41500000",
    "Area": "60",
    "UnitPrice": "691666",
    "FloorPlan": "3LDK",
    "BuildingYear": "2003年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "5",
    "Period": "2023年第3四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "牡丹",
    "TradePrice": "42300000",
    "Area": "48",
    "UnitPrice": "881250",
    "FloorPlan": "2LDK",
    "BuildingYear": "2007年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "11",
    "Period": "2025年第4四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "牡丹",
    "TradePrice": "26500000",
    "Area": "46",
    "UnitPrice": "576086",
    "FloorPlan": "3LDK",
    "BuildingYear": "1992年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "9",
    "Period": "2025年第2四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "48500000",
    "Area": "66",
    "UnitPrice": "734848",
    "FloorPlan": "3LDK",
    "BuildingYear": "1994年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "15",
    "Period": "2025年第1四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "枝川",
    "TradePrice": "35200000",
    "Area": "47",
    "UnitPrice": "748936",
    "FloorPlan": "3LDK",
    "BuildingYear": "2002年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "13",
    "Period": "2025年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "新大橋",
    "TradePrice": "41200000",
    "Area": "70",
    "UnitPrice": "588571",
    "FloorPlan": "3LDK",
    "BuildingYear": "1991年",
    "Structure": "ＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "8",
    "Period": "2025年第1四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "深川",
    "TradePrice": "39100000",
    "Area": "53",
    "UnitPrice": "737735",
    "FloorPlan": "4LDK",
    "BuildingYear": "2004年",
    "Structure": "ＲＣ",
    "NearestStation": "辰巳",
    "TimeToNearestStation": "15",
    "Period": "2022年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "牡丹",
    "TradePrice": "45000000",
    "Area": "48",
    "UnitPrice": "937500",
    "FloorPlan": "2LDK",
    "BuildingYear": "2015年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "14",
    "Period": "2025年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "49400000",
    "Area": "60",
    "UnitPrice": "823333",
    "FloorPlan": "2LDK",
    "BuildingYear": "2004年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "3",
    "Period": "2022年第4四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "31200000",
    "Area": "53",
    "UnitPrice": "588679",
    "FloorPlan": "1LDK",
    "BuildingYear": "1988年",
    "Structure": "ＳＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "11",
    "Period": "2023年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "深川",
    "TradePrice": "46300000",
    "Area": "55",
    "UnitPrice": "841818",
    "FloorPlan": "4LDK",
    "BuildingYear": "2008年",
    "Structure": "ＳＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "4",
    "Period": "2023年第4四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "67500000",
    "Area": "72",
    "UnitPrice": "937500",
    "FloorPlan": "1LDK",
    "BuildingYear": "2017年",
    "Structure": "ＳＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "15",
    "Period": "2025年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東陽",
    "TradePrice": "47600000",
    "Area": "53",
    "UnitPrice": "898113",
    "FloorPlan": "3LDK",
    "BuildingYear": "2017年",
    "Structure": "ＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "10",
    "Period": "2023年第4四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "30800000",
    "Area": "47",
    "UnitPrice": "655319",
    "FloorPlan": "2LDK",
    "BuildingYear": "1988年",
    "Structure": "ＳＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "10",
    "Period": "2022年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東陽",
    "TradePrice": "78800000",
    "Area": "82",
    "UnitPrice": "960975",
    "FloorPlan": "4LDK",
    "BuildingYear": "2010年",
    "Structure": "ＳＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "9",
    "Period": "2024年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "豊洲",
    "TradePrice": "45300000",
    "Area": "72",
    "UnitPrice": "629166",
    "FloorPlan": "3LDK",
    "BuildingYear": "1988年",
    "Structure": "ＳＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "3",
    "Period": "2022年第2四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "46200000",
    "Area": "65",
    "UnitPrice": "710769",
    "FloorPlan": "3LDK",
    "BuildingYear": "1993年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "9",
    "Period": "2023年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東雲",
    "TradePrice": "82900000",
    "Area": "85",
    "UnitPrice": "975294",
    "FloorPlan": "3LDK",
    "BuildingYear": "2016年",
    "Structure": "ＲＣ",
    "NearestStation": "辰巳",
    "TimeToNearestStation": "12",
    "Period": "2025年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東陽",
    "TradePrice": "34300000",
    "Area": "57",
    "UnitPrice": "601754",
    "FloorPlan": "3LDK",
    "BuildingYear": "1990年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "10",
    "Period": "2023年第3四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "73000000",
    "Area": "85",
    "UnitPrice": "858823",
    "FloorPlan": "3LDK",
    "BuildingYear": "2003年",
    "Structure": "ＳＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "8",
    "Period": "2022年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "豊洲",
    "TradePrice": "79400000",
    "Area": "82",
    "UnitPrice": "968292",
    "FloorPlan": "3LDK",
    "BuildingYear": "2019年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "13",
    "Period": "2025年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "枝川",
    "TradePrice": "75100000",
    "Area": "85",
    "UnitPrice": "883529",
    "FloorPlan": "2LDK",
    "BuildingYear": "2017年",
    "Structure": "ＳＲＣ",
    "NearestStation": "辰巳",
    "TimeToNearestStation": "6",
    "Period": "2025年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "豊洲",
    "TradePrice": "40100000",
    "Area": "51",
    "UnitPrice": "786274",
    "FloorPlan": "1LDK",
    "BuildingYear": "2002年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "7",
    "Period": "2024年第4四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "深川",
    "TradePrice": "46100000",
    "Area": "42",
    "UnitPrice": "1097619",
    "FloorPlan": "3LDK",
    "BuildingYear": "2021年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "11",
    "Period": "2023年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "豊洲",
    "TradePrice": "55200000",
    "Area": "47",
    "UnitPrice": "1174468",
    "FloorPlan": "4LDK",
    "BuildingYear": "2023年",
    "Structure": "ＳＲＣ",
    "NearestStation": "辰巳",
    "TimeToNearestStation": "11",
    "Period": "2025年第2四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "塩浜",
    "TradePrice": "51100000",
    "Area": "62",
    "UnitPrice": "824193",
    "FloorPlan": "3LDK",
    "BuildingYear": "2014年",
    "Structure": "ＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "8",
    "Period": "2024年第1四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "枝川",
    "TradePrice": "51200000",
    "Area": "83",
    "UnitPrice": "616867",
    "FloorPlan": "4LDK",
    "BuildingYear": "1988年",
    "Structure": "ＲＣ",
    "NearestStation": "越中島",
    "TimeToNearestStation": "3",
    "Period": "2023年第2四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "枝川",
    "TradePrice": "65700000",
    "Area": "76",
    "UnitPrice": "864473",
    "FloorPlan": "4LDK",
    "BuildingYear": "2012年",
    "Structure": "ＲＣ",
    "NearestStation": "豊洲",
    "TimeToNearestStation": "9",
    "Period": "2024年第2四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "東陽",
    "TradePrice": "77600000",
    "Area": "81",
    "UnitPrice": "958024",
    "FloorPlan": "4LDK",
    "BuildingYear": "2021年",
    "Structure": "ＲＣ",
    "NearestStation": "東陽町",
    "TimeToNearestStation": "3",
    "Period": "2024年第4四半期",
    "PriceCategory": "不動産取引価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  },
  {
    "Type": "中古マンション等",
    "DistrictName": "牡丹",
    "TradePrice": "50300000",
    "Area": "60",
    "UnitPrice": "838333",
    "FloorPlan": "3LDK",
    "BuildingYear": "2011年",
    "Structure": "ＲＣ",
    "NearestStation": "門前仲町",
    "TimeToNearestStation": "3",
    "Period": "2024年第3四半期",
    "PriceCategory": "成約価格情報",
    "Municipality": "江東区",
    "Prefecture": "東京都"
  }
]'''


"""
国土交通省「不動産情報ライブラリ」(reinfolib) API クライアント。

利用するエンドポイント:
  - XIT001 : 不動産価格（取引価格・成約価格）情報取得
  - XIT002 : 都道府県内市区町村一覧取得（市区町村コードの解決に使用）

APIキー（無料・申請制、発行まで約5営業日）は環境変数 `REINFOLIB_API_KEY` で渡す。
リクエスト時は HTTP ヘッダ `Ocp-Apim-Subscription-Key` にキーを設定する。

キーが無い／テストしたい場合は use_mock=True でサンプル成約データ(sample_comps.json)を返せる。

出典: 国土交通省 不動産情報ライブラリ
  https://www.reinfolib.mlit.go.jp/help/apiManual/xit001/
"""


import json
import os
import re
from dataclasses import dataclass

from functools import lru_cache
from pathlib import Path
from typing import Optional

import requests

BASE_URL = "https://www.reinfolib.mlit.go.jp/ex-api/external"
TIMEOUT = 20

# 価格情報区分コード
PRICE_TRADE = "01"   # 不動産取引価格情報
PRICE_DEAL = "02"    # 成約価格情報（2021年以降）

# 都道府県名 -> 2桁コード
PREFECTURE_CODES = {
    "北海道": "01", "青森県": "02", "岩手県": "03", "宮城県": "04", "秋田県": "05",
    "山形県": "06", "福島県": "07", "茨城県": "08", "栃木県": "09", "群馬県": "10",
    "埼玉県": "11", "千葉県": "12", "東京都": "13", "神奈川県": "14", "新潟県": "15",
    "富山県": "16", "石川県": "17", "福井県": "18", "山梨県": "19", "長野県": "20",
    "岐阜県": "21", "静岡県": "22", "愛知県": "23", "三重県": "24", "滋賀県": "25",
    "京都府": "26", "大阪府": "27", "兵庫県": "28", "奈良県": "29", "和歌山県": "30",
    "鳥取県": "31", "島根県": "32", "岡山県": "33", "広島県": "34", "山口県": "35",
    "徳島県": "36", "香川県": "37", "愛媛県": "38", "高知県": "39", "福岡県": "40",
    "佐賀県": "41", "長崎県": "42", "熊本県": "43", "大分県": "44", "宮崎県": "45",
    "鹿児島県": "46", "沖縄県": "47",
}

_PREF_PATTERN = re.compile(
    "(" + "|".join(map(re.escape, PREFECTURE_CODES.keys())) + ")"
)


class ReinfolibError(RuntimeError):
    pass


@dataclass
class Comp:
    """成約・取引事例 1件。マンション相場比較に必要な項目だけを保持する。"""
    unit_price: float          # ㎡単価（円/㎡）
    trade_price: Optional[int] # 取引総額（円）
    area: Optional[float]      # 専有面積（㎡）
    age: Optional[int]         # 取引時点での築年数（年）
    building_year: Optional[int]
    floor_plan: str
    district: str              # 地区名
    station: str               # 最寄駅
    walk_min: Optional[int]    # 駅徒歩（分）
    period: str                # 取引時点（例 "2024年第2四半期"）
    structure: str
    is_deal: bool              # True=成約価格, False=取引価格


# --------------------------------------------------------------------------- #
# APIキー
# --------------------------------------------------------------------------- #

def api_key() -> Optional[str]:
    return os.environ.get("REINFOLIB_API_KEY")


def _request(endpoint: str, params: dict) -> dict:
    key = api_key()
    if not key:
        raise ReinfolibError(
            "REINFOLIB_API_KEY が未設定です。不動産情報ライブラリでAPIキーを申請し、"
            "環境変数に設定してください（テストは use_mock=True を利用）。"
        )
    headers = {"Ocp-Apim-Subscription-Key": key}
    # requests は Content-Encoding: gzip を自動デコードする
    resp = requests.get(f"{BASE_URL}/{endpoint}", headers=headers,
                        params=params, timeout=TIMEOUT)
    if resp.status_code == 401:
        raise ReinfolibError("APIキーが無効です（401）。キーを確認してください。")
    if resp.status_code != 200:
        raise ReinfolibError(f"APIエラー {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    if body.get("status") not in ("OK", None):
        raise ReinfolibError(f"APIステータス異常: {body.get('status')}")
    return body


# --------------------------------------------------------------------------- #
# 市区町村コードの解決
# --------------------------------------------------------------------------- #

def split_prefecture(address: str) -> tuple[Optional[str], str]:
    """住所文字列から (都道府県名, 残り) を取り出す。"""
    m = _PREF_PATTERN.search(address)
    if not m:
        return None, address
    pref = m.group(1)
    rest = address[m.end():]
    return pref, rest


@lru_cache(maxsize=64)
def list_cities(pref_code: str) -> tuple[tuple[str, str], ...]:
    """XIT002: 都道府県内の (市区町村コード, 名称) 一覧。lru_cacheで再利用。"""
    body = _request("XIT002", {"area": pref_code})
    out = []
    for row in body.get("data", []):
        cid = row.get("id") or row.get("MunicipalityCode") or row.get("code")
        name = row.get("name") or row.get("Municipality")
        if cid and name:
            out.append((str(cid), str(name)))
    return tuple(out)


def resolve_city_code(address: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    住所から (都道府県コード, 市区町村コード, 市区町村名) を解決する。
    郡部（例: 西多摩郡瑞穂町）も最長前方一致でマッチさせる。
    """
    pref, rest = split_prefecture(address)
    if not pref:
        return None, None, None
    pref_code = PREFECTURE_CODES[pref]
    try:
        cities = list_cities(pref_code)
    except ReinfolibError:
        return pref_code, None, None

    best = None  # (一致長, code, name)
    for code, name in cities:
        if rest.startswith(name) and (best is None or len(name) > best[0]):
            best = (len(name), code, name)
    if best:
        return pref_code, best[1], best[2]
    return pref_code, None, None


# --------------------------------------------------------------------------- #
# 取引・成約価格の取得
# --------------------------------------------------------------------------- #

_WAREKI = {"令和": 2018, "平成": 1988, "昭和": 1925}


def _to_west_year(s: str) -> Optional[int]:
    """ "平成20年" / "平成21年3月" / "2008年" / "令和元年" → 西暦 """
    if not s:
        return None
    s = s.strip()
    for era, base in _WAREKI.items():
        if era in s:
            if "元" in s:
                return base + 1
            # 元号直後の数字だけを取る（"平成21年3月" の月を巻き込まない）
            m = re.search(era + r"\s*(\d+)", s)
            return base + int(m.group(1)) if m else base + 1
    m = re.search(r"(19|20)\d{2}", s)
    return int(m.group()) if m else None


def _period_year(period: str) -> Optional[int]:
    m = re.search(r"(19|20)\d{2}", period or "")
    return int(m.group()) if m else None


def _to_int(s) -> Optional[int]:
    if s in (None, ""):
        return None
    try:
        return int(float(str(s).replace(",", "")))
    except ValueError:
        return None


def _to_float(s) -> Optional[float]:
    if s in (None, ""):
        return None
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def _row_to_comp(row: dict) -> Optional[Comp]:
    """XIT001 の 1レコード → Comp（中古マンションのみ）。"""
    type_ = row.get("Type", "")
    if "マンション" not in type_:
        return None

    area = _to_float(row.get("Area"))
    trade_price = _to_int(row.get("TradePrice"))
    unit_price = _to_float(row.get("UnitPrice"))
    if not unit_price and trade_price and area:
        unit_price = trade_price / area
    if not unit_price or unit_price <= 0:
        return None

    building_year = _to_west_year(row.get("BuildingYear", ""))
    period_year = _period_year(row.get("Period", ""))
    age = None
    if building_year and period_year:
        age = max(0, period_year - building_year)

    return Comp(
        unit_price=unit_price,
        trade_price=trade_price,
        area=area,
        age=age,
        building_year=building_year,
        floor_plan=row.get("FloorPlan", "") or "",
        district=row.get("DistrictName", "") or "",
        station=row.get("NearestStation", "") or row.get("最寄駅：名称", "") or "",
        walk_min=_to_int(row.get("TimeToNearestStation")),
        period=row.get("Period", "") or "",
        structure=row.get("Structure", "") or "",
        is_deal=("成約" in (row.get("PriceCategory", "") or "")),
    )


def fetch_comps(
    city_code: str,
    years: Optional[list[int]] = None,
    include_trade: bool = True,
    use_mock: bool = False,
) -> list[Comp]:
    """
    指定市区町村の中古マンション事例（成約優先）を取得する。

    - まず成約価格(02)を新しい年から取得
    - 件数が少なければ取引価格(01)も足す（include_trade=True）
    """
    if use_mock:
        return _load_mock_comps()

    if years is None:
        this_year = _dt.now().year
        years = list(range(this_year, this_year - 5, -1))  # 直近5年

    comps: list[Comp] = []

    # 成約価格（2021年以降のみ存在）
    for y in years:
        if y < 2021:
            continue
        body = _request("XIT001", {
            "year": str(y), "city": city_code, "priceClassification": PRICE_DEAL,
        })
        for row in body.get("data", []):
            c = _row_to_comp(row)
            if c:
                c.is_deal = True
                comps.append(c)

    # 事例が薄ければ取引価格も補完
    if include_trade and len(comps) < 15:
        for y in years:
            body = _request("XIT001", {
                "year": str(y), "city": city_code, "priceClassification": PRICE_TRADE,
            })
            for row in body.get("data", []):
                c = _row_to_comp(row)
                if c:
                    comps.append(c)

    return comps


# --------------------------------------------------------------------------- #
# モック（APIキー無しのテスト用）
# --------------------------------------------------------------------------- #

def _load_mock_comps() -> list[Comp]:
    rows = json.loads(_SAMPLE_COMPS_JSON)
    out = []
    for r in rows:
        c = _row_to_comp(r)
        if c:
            out.append(c)
    return out

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


import re
from dataclasses import dataclass, asdict

from typing import Optional

import requests
from bs4 import BeautifulSoup

USER_AGENT = (
    "Mozilla/5.0 (compatible; value-scan/1.0; +contact@example.com) "
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
        return max(0, _dt.now().year - self.built_year)

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

"""
相場推定と割安判定ロジック。

考え方:
  1. 対象マンションと同一市区町村の中古マンション成約・取引事例(Comp)を集める
  2. 外れ値（IQR）を除去
  3. 築年で㎡単価を補正して「対象の築年における推定㎡単価」を求める
       - 事例が十分あれば 単価 = b0 + b1*築年 の最小二乗回帰
       - 少なければ 類似事例の中央値 × 築年補正係数
  4. 推定㎡単価 × 専有面積 = 推定相場価格
  5. 売出価格 ÷ 推定相場 = 割安率 → グレード(A〜E)

純Pythonのみ（numpy不要）。データ出典は国土交通省の取引・成約価格情報。
"""


import math
import statistics
from dataclasses import dataclass, field
from typing import Optional


MIN_FOR_REGRESSION = 12     # これ以上なら回帰を使う
MIN_COMPS = 4               # これ未満なら判定不能


# --------------------------------------------------------------------------- #
# 統計ヘルパ（純Python）
# --------------------------------------------------------------------------- #

def _quantile(xs: list[float], q: float) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return s[int(pos)]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _iqr_filter(comps: list[Comp]) -> list[Comp]:
    """㎡単価のIQRで外れ値を除去。"""
    prices = [c.unit_price for c in comps]
    if len(prices) < 4:
        return comps
    q1, q3 = _quantile(prices, 0.25), _quantile(prices, 0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [c for c in comps if lo <= c.unit_price <= hi]


def _linregress(xs: list[float], ys: list[float]) -> Optional[tuple[float, float]]:
    """最小二乗で y = b0 + b1*x の (b0, b1) を返す。分散ゼロならNone。"""
    n = len(xs)
    if n < 3:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b1 = sxy / sxx
    b0 = my - b1 * mx
    return b0, b1


# 築年補正係数（フォールバック用の一般的な中古マンション減価カーブ）
def depreciation_factor(age: Optional[int]) -> float:
    if age is None:
        age = 25
    age = max(0, age)
    if age <= 30:
        f = 1.0 - 0.013 * age          # 〜30年: 約1.3%/年
    else:
        f = (1.0 - 0.013 * 30) - 0.004 * (age - 30)  # 以降は緩やか
    return max(0.45, min(1.05, f))


# --------------------------------------------------------------------------- #
# 結果
# --------------------------------------------------------------------------- #

GRADES = [
    # (上限ratio, grade, ラベル, 色)
    (0.85, "A", "非常に割安", "#1aa260"),
    (0.93, "B", "割安",       "#3ac17a"),
    (1.02, "C", "ほぼ適正",   "#2b8cd9"),
    (1.12, "D", "やや割高",   "#e8943a"),
    (9.99, "E", "割高",       "#d9534f"),
]


@dataclass
class Appraisal:
    ok: bool
    message: str = ""
    estimated_unit_price: Optional[float] = None   # 推定㎡単価（円/㎡）
    estimated_price: Optional[int] = None          # 推定相場（円）
    price_low: Optional[int] = None                # 推定レンジ下限
    price_high: Optional[int] = None               # 推定レンジ上限
    asking_price: Optional[int] = None             # 売出価格
    ratio: Optional[float] = None                  # 売出 ÷ 推定
    diff_yen: Optional[int] = None                 # 売出 − 推定（負=割安）
    discount_pct: Optional[float] = None           # 割安率(%) 正=割安
    grade: Optional[str] = None
    grade_label: str = ""
    grade_color: str = ""
    confidence: str = ""                           # 高 / 中 / 低
    n_comps: int = 0
    n_deals: int = 0
    method: str = ""
    representative: list[Comp] = field(default_factory=list)


def _grade_for(ratio: float) -> tuple[str, str, str]:
    for upper, g, label, color in GRADES:
        if ratio <= upper:
            return g, label, color
    return "E", "割高", "#d9534f"


def _confidence(n: int, cv: float) -> str:
    if n >= 20 and cv <= 0.28:
        return "高"
    if n >= 8 and cv <= 0.45:
        return "中"
    return "低"


def _similar(comps: list[Comp], age: Optional[int], area: Optional[float]) -> list[Comp]:
    """築年±15年・面積±50%で類似事例を抽出（足りなければ緩める）。"""
    def near(c: Comp) -> bool:
        if age is not None and c.age is not None and abs(c.age - age) > 15:
            return False
        if area and c.area and not (0.5 * area <= c.area <= 1.6 * area):
            return False
        return True

    narrowed = [c for c in comps if near(c)]
    return narrowed if len(narrowed) >= MIN_COMPS else comps


# --------------------------------------------------------------------------- #
# メイン
# --------------------------------------------------------------------------- #

def appraise(
    area_m2: Optional[float],
    age: Optional[int],
    asking_price: Optional[int],
    comps: list[Comp],
) -> Appraisal:
    if not area_m2 or not asking_price:
        return Appraisal(ok=False, message="専有面積または売出価格が不明です。")

    comps = [c for c in comps if c.unit_price and c.unit_price > 0]
    n_deals = sum(1 for c in comps if c.is_deal)
    comps = _iqr_filter(comps)
    if len(comps) < MIN_COMPS:
        return Appraisal(
            ok=False,
            n_comps=len(comps), n_deals=n_deals,
            message=("周辺の取引事例が不足しているため判定できませんでした"
                     f"（有効事例 {len(comps)} 件）。地方や事例の少ないエリアで起こりえます。"),
        )

    used = _similar(comps, age, area_m2)
    unit_prices = [c.unit_price for c in used]
    mean_up = statistics.fmean(unit_prices)
    cv = (statistics.pstdev(unit_prices) / mean_up) if mean_up else 1.0

    # --- 推定㎡単価 ---
    est_unit = None
    method = ""
    aged = [(c.age, c.unit_price) for c in used if c.age is not None]
    if len(aged) >= MIN_FOR_REGRESSION and age is not None:
        reg = _linregress([a for a, _ in aged], [u for _, u in aged])
        if reg:
            b0, b1 = reg
            pred = b0 + b1 * age
            lo = _quantile([u for _, u in aged], 0.05)
            hi = _quantile([u for _, u in aged], 0.95)
            if b1 <= 0 and lo <= pred <= hi:   # 妥当（古いほど安い）な場合のみ採用
                est_unit = pred
                method = f"築年回帰（{len(aged)}件）"

    if est_unit is None:
        # フォールバック: 類似事例の中央値を築年補正
        med_up = statistics.median(unit_prices)
        ages = [c.age for c in used if c.age is not None]
        base_age = statistics.median(ages) if ages else 25
        adj = depreciation_factor(age) / depreciation_factor(int(base_age))
        est_unit = med_up * adj
        method = f"類似中央値×築年補正（{len(used)}件）"

    estimated_price = int(est_unit * area_m2)

    # --- 割安判定 ---
    ratio = asking_price / estimated_price
    grade, label, color = _grade_for(ratio)
    diff = asking_price - estimated_price
    discount = (1 - ratio) * 100

    band = max(0.08, min(0.25, cv * 0.8))
    confidence = _confidence(len(used), cv)

    # --- 代表的な成約事例（類似順 上位5件） ---
    def sim_key(c: Comp):
        da = abs((c.age or 999) - (age or 0))
        dar = abs((c.area or 0) - area_m2)
        return (0 if c.is_deal else 1, da, dar)

    representative = sorted(used, key=sim_key)[:5]

    return Appraisal(
        ok=True,
        estimated_unit_price=est_unit,
        estimated_price=estimated_price,
        price_low=int(estimated_price * (1 - band)),
        price_high=int(estimated_price * (1 + band)),
        asking_price=asking_price,
        ratio=ratio,
        diff_yen=diff,
        discount_pct=discount,
        grade=grade,
        grade_label=label,
        grade_color=color,
        confidence=confidence,
        n_comps=len(comps),
        n_deals=n_deals,
        method=method,
        representative=representative,
    )


# --------------------------------------------------------------------------- #
# 表示用フォーマット
# --------------------------------------------------------------------------- #

def yen_man(yen: Optional[int]) -> str:
    """円 → 「○,○○○万円」/「○億○,○○○万円」"""
    if yen is None:
        return "—"
    man = round(yen / 1_0000)
    if man >= 1_0000:
        oku, rest = divmod(man, 1_0000)
        return f"{oku}億{rest:,}万円" if rest else f"{oku}億円"
    return f"{man:,}万円"

from dataclasses import dataclass
from typing import Optional

SAMPLE_PROPERTY = Property(
    name="サンプルレジデンス豊洲（デモ）", price_yen=52_800_000,
    address="東京都江東区豊洲4丁目", area_m2=68.0, floor_plan="3LDK",
    built_year=2009, built_month=3, floor=12,
    station="東京メトロ有楽町線 豊洲駅 徒歩8分", walk_min=8, structure="ＲＣ",
    url="https://suumo.jp/ms/chuko/")

@dataclass
class Result:
    ok: bool
    message: str = ""
    prop: Optional[Property] = None
    appraisal: Optional[Appraisal] = None
    city_name: Optional[str] = None
    demo: bool = False

def appraise_from_url(url, use_mock=False):
    prop = None
    try:
        prop = fetch_property(url)
    except PropertyParseError as e:
        if not use_mock:
            return Result(ok=False, message=str(e))
    except Exception as e:
        if not use_mock:
            return Result(ok=False, message=f"ページ取得エラー: {e}")
    if prop is None:
        return _appraise(SAMPLE_PROPERTY, use_mock=True, demo=True)
    return _appraise(prop, use_mock=use_mock)

def appraise_manual(prop, use_mock=False):
    return _appraise(prop, use_mock=use_mock, demo=use_mock)

def _appraise(prop, use_mock=False, demo=False):
    city_name = None
    city_code = None
    if not use_mock:
        try:
            _, city_code, city_name = resolve_city_code(prop.address)
        except ReinfolibError as e:
            return Result(ok=False, prop=prop, message=str(e))
        if not city_code:
            return Result(ok=False, prop=prop, message="所在地から市区町村を特定できませんでした。")
    else:
        city_name = "東京都江東区（サンプル）"
    try:
        comps = fetch_comps(city_code or "00000", use_mock=use_mock)
    except ReinfolibError as e:
        return Result(ok=False, prop=prop, city_name=city_name, message=str(e))
    ap = appraise(prop.area_m2, prop.age, prop.price_yen, comps)
    if not ap.ok:
        return Result(ok=False, prop=prop, city_name=city_name, appraisal=ap, message=ap.message, demo=demo)
    return Result(ok=True, prop=prop, appraisal=ap, city_name=city_name, demo=demo)

"""
LINE Flex Message（割安判定カード）の組み立て。
Result から LINE の messages 配列を作る。
"""




def _row(label: str, value: str, value_color: str = "#333333", bold: bool = False) -> dict:
    return {
        "type": "box", "layout": "baseline", "spacing": "sm",
        "contents": [
            {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 4},
            {"type": "text", "text": value, "size": "sm", "color": value_color,
             "flex": 6, "weight": "bold" if bold else "regular", "wrap": True, "align": "end"},
        ],
    }


def build_result_flex(result: Result) -> dict:
    prop = result.prop
    ap = result.appraisal
    name = (prop.name if prop else "物件")[:34]

    # ---- ヘッダ（グレード色） ----
    header = {
        "type": "box", "layout": "vertical", "backgroundColor": ap.grade_color,
        "paddingAll": "16px", "spacing": "xs",
        "contents": [
            {"type": "text", "text": "VALUE SCAN 割安度判定", "color": "#ffffffcc", "size": "xs"},
            {"type": "text", "text": name, "color": "#ffffff", "size": "md",
             "weight": "bold", "wrap": True},
            {"type": "box", "layout": "baseline", "spacing": "md", "margin": "md",
             "contents": [
                 {"type": "text", "text": ap.grade, "color": "#ffffff", "size": "4xl",
                  "weight": "bold", "flex": 0},
                 {"type": "text", "text": ap.grade_label, "color": "#ffffff", "size": "lg",
                  "weight": "bold", "gravity": "center"},
             ]},
        ],
    }

    # ---- 差額表現 ----
    if ap.discount_pct >= 0:
        diff_text = f"相場より {yen_man(abs(ap.diff_yen))} 割安（▼{ap.discount_pct:.0f}%）"
        diff_color = "#1aa260"
    else:
        diff_text = f"相場より {yen_man(abs(ap.diff_yen))} 割高（▲{abs(ap.discount_pct):.0f}%）"
        diff_color = "#d9534f"

    body_contents = [
        _row("売出価格", yen_man(ap.asking_price), "#111111", bold=True),
        _row("推定相場", yen_man(ap.estimated_price), "#111111", bold=True),
        _row("推定レンジ", f"{yen_man(ap.price_low)}〜{yen_man(ap.price_high)}"),
        {"type": "box", "layout": "vertical", "margin": "md", "paddingAll": "10px",
         "backgroundColor": "#f3faf5" if ap.discount_pct >= 0 else "#fdf2f2",
         "cornerRadius": "8px",
         "contents": [
             {"type": "text", "text": diff_text, "size": "sm", "weight": "bold",
              "color": diff_color, "wrap": True, "align": "center"},
         ]},
        {"type": "separator", "margin": "lg"},
    ]

    # ---- 物件スペック ----
    specs = []
    if prop:
        if prop.area_m2:
            specs.append(_row("専有面積", f"{prop.area_m2:.0f}㎡"))
        if prop.floor_plan:
            specs.append(_row("間取り", prop.floor_plan))
        if prop.age is not None:
            specs.append(_row("築年数", f"築{prop.age}年（{prop.built_year}年）"))
        loc = result.city_name or ""
        if loc:
            specs.append(_row("エリア", loc))
    body_contents += specs
    body_contents.append({"type": "separator", "margin": "lg"})

    # ---- 成約事例 ----
    body_contents.append(
        {"type": "text", "text": f"周辺の取引・成約事例（{ap.n_comps}件中）",
         "size": "sm", "weight": "bold", "color": "#2b8cd9", "margin": "md"})
    for c in ap.representative[:3]:
        tag = "成約" if c.is_deal else "取引"
        area = f"{c.area:.0f}㎡" if c.area else "—"
        age = f"築{c.age}" if c.age is not None else ""
        line = f"[{tag}] {yen_man(c.trade_price)} / {area} {age} / {c.station or c.district}"
        body_contents.append(
            {"type": "text", "text": line, "size": "xs", "color": "#555555",
             "wrap": True, "margin": "sm"})

    body_contents.append(
        {"type": "text",
         "text": f"判定根拠: {ap.method}・信頼度 {ap.confidence}",
         "size": "xxs", "color": "#aaaaaa", "margin": "md", "wrap": True})

    body = {"type": "box", "layout": "vertical", "paddingAll": "16px",
            "spacing": "sm", "contents": body_contents}

    # ---- フッタ ----
    footer_contents = []
    if prop and prop.url:
        footer_contents.append({
            "type": "button", "style": "primary", "height": "sm",
            "color": ap.grade_color,
            "action": {"type": "uri", "label": "SUUMOで物件を見る", "uri": prop.url},
        })
    footer_contents.append({
        "type": "text",
        "text": "推定値です。実際の価値は個別条件で変動します。データ出典: 国土交通省",
        "size": "xxs", "color": "#aaaaaa", "wrap": True, "margin": "sm"})
    footer = {"type": "box", "layout": "vertical", "paddingAll": "12px",
            "spacing": "sm", "contents": footer_contents}

    bubble = {"type": "bubble", "size": "mega",
            "header": header, "body": body, "footer": footer}

    return {
        "type": "flex",
        "altText": f"{name} の割安度: {ap.grade}（{ap.grade_label}）",
        "contents": bubble,
    }


def build_messages(result: Result) -> list[dict]:
    """成功時はFlex、失敗時はテキストを返す。"""
    if result.ok:
        return [build_result_flex(result)]
    return [{"type": "text", "text": "⚠️ " + (result.message or "判定できませんでした。")}]


WELCOME_TEXT = (
    "VALUE SCANへようこそ🏢\n\n"
    "気になる中古マンションの【SUUMOのURL】をそのまま送ってください。\n"
    "周辺の取引・成約事例から、割安/割高度を判定します。\n\n"
    "※判定は推定値です。データ出典: 国土交通省 不動産情報ライブラリ"
)

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VALUE SCAN｜マンション割安判定サービス</title>
<style>
  :root{
    --blue:#2b8cd9; --blue-d:#1f6fb2; --green:#06c755; --green-d:#05a648;
    --ink:#1b2733; --muted:#6b7785; --line:#e6ebf0; --bg:#f5f8fb;
  }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Noto Sans JP",sans-serif;
       color:var(--ink);background:var(--bg);line-height:1.6}
  .hero{background:linear-gradient(160deg,#5db4f0 0%,#2b8cd9 45%,#1f6fb2 100%);
        color:#fff;padding:48px 20px 64px;text-align:center;position:relative;overflow:hidden}
  .hero::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:40px;
        background:var(--bg);border-radius:50% 50% 0 0/100% 100% 0 0}
  .logo{font-weight:800;font-size:13px;letter-spacing:2px;opacity:.9}
  .hero h1{font-size:26px;margin:8px 0 4px;font-weight:800}
  .hero .en{font-style:italic;font-weight:800;font-size:40px;letter-spacing:1px;
        text-shadow:0 2px 8px rgba(0,0,0,.15);margin:2px 0}
  .hero p{margin:10px auto 0;max-width:560px;font-size:14px;opacity:.95}
  .badges{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:14px}
  .badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.4);
        padding:5px 12px;border-radius:999px;font-size:12px;font-weight:600}
  .wrap{max-width:620px;margin:-32px auto 0;padding:0 16px 64px;position:relative;z-index:2}
  .card{background:#fff;border:1px solid var(--line);border-radius:16px;
        box-shadow:0 10px 30px rgba(31,111,178,.10);padding:22px}
  .card h2{font-size:16px;margin:0 0 4px}
  .card .sub{color:var(--muted);font-size:13px;margin:0 0 14px}
  .field{display:flex;gap:8px;flex-wrap:wrap}
  input[type=url]{flex:1;min-width:0;padding:13px 14px;border:1.5px solid var(--line);
        border-radius:10px;font-size:15px;outline:none}
  input[type=url]:focus{border-color:var(--blue)}
  button{cursor:pointer;border:0;border-radius:10px;font-weight:700;font-size:15px}
  .btn-go{background:var(--green);color:#fff;padding:13px 22px}
  .btn-go:hover{background:var(--green-d)}
  .btn-go:disabled{opacity:.6;cursor:wait}
  .demo{display:inline-block;margin-top:12px;color:var(--blue-d);font-size:13px;
        background:none;text-decoration:underline}
  .note{margin-top:14px;color:var(--muted);font-size:11.5px}
  #result{margin-top:22px}
  .res-card{background:#fff;border:1px solid var(--line);border-radius:16px;overflow:hidden;
        box-shadow:0 10px 30px rgba(0,0,0,.08)}
  .res-head{padding:22px;color:#fff}
  .res-head .pname{font-size:14px;opacity:.92;font-weight:600}
  .grade-row{display:flex;align-items:baseline;gap:12px;margin-top:6px}
  .grade{font-size:54px;font-weight:800;line-height:1}
  .grade-label{font-size:20px;font-weight:800}
  .verdict{margin-top:10px;font-size:15px;font-weight:700}
  .res-body{padding:20px 22px}
  .prices{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:6px}
  .pbox{background:var(--bg);border-radius:12px;padding:12px 14px}
  .pbox .l{font-size:12px;color:var(--muted)}
  .pbox .v{font-size:20px;font-weight:800;margin-top:2px}
  .range{font-size:12px;color:var(--muted);margin:2px 0 14px}
  .spec{display:flex;flex-wrap:wrap;gap:6px 16px;font-size:13px;color:#445;
        border-top:1px solid var(--line);padding-top:14px}
  .spec b{color:var(--ink)}
  .comps{margin-top:16px}
  .comps h3{font-size:13px;color:var(--blue-d);margin:0 0 8px}
  .comp{display:flex;justify-content:space-between;gap:10px;font-size:12.5px;
        padding:8px 0;border-bottom:1px dashed var(--line)}
  .comp .tag{display:inline-block;background:#eaf4fc;color:var(--blue-d);
        border-radius:6px;padding:1px 6px;font-size:11px;margin-right:6px;font-weight:700}
  .comp .tag.deal{background:#e7f8ee;color:var(--green-d)}
  .meta{font-size:11px;color:var(--muted);margin-top:14px}
  .res-foot{padding:14px 22px;background:var(--bg);font-size:11px;color:var(--muted)}
  .res-foot a{color:var(--blue-d)}
  .err{background:#fdf2f2;border:1px solid #f3c9c9;color:#b3433f;border-radius:12px;
        padding:16px;font-size:14px}
  .loading{text-align:center;color:var(--muted);padding:24px;font-size:14px}
  .spinner{width:26px;height:26px;border:3px solid var(--line);border-top-color:var(--blue);
        border-radius:50%;animation:sp .8s linear infinite;margin:0 auto 10px}
  @keyframes sp{to{transform:rotate(360deg)}}
  .steps{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px}
  .step{background:#fff;border:1px solid var(--line);border-radius:12px;padding:12px;text-align:center}
  .step .n{width:24px;height:24px;border-radius:50%;background:var(--blue);color:#fff;
        font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;margin:0 auto 6px}
  .step .t{font-size:12px;color:var(--muted)}
  footer.site{text-align:center;color:var(--muted);font-size:11px;padding:24px}
</style>
</head>
<body>
  <header class="hero">
    <div class="logo">🏢 VALUE SCAN</div>
    <h1>マンション割安判定サービス</h1>
    <div class="en">VALUE SCAN</div>
    <p>気になる中古マンションの <b>SUUMOリンクを貼るだけ</b>。<br>
       周辺の取引・成約事例から、割安／割高をすぐに判定します。</p>
    <div class="badges">
      <span class="badge">登録不要</span>
      <span class="badge">回数無制限</span>
      <span class="badge">データ出典：国土交通省</span>
    </div>
  </header>

  <main class="wrap">
    <section class="card">
      <h2>SUUMOのURLで割安度をチェック</h2>
      <p class="sub">中古マンションの物件ページURLを貼り付けてください。</p>
      <form id="form" class="field">
        <input id="url" type="url" placeholder="https://suumo.jp/ms/chuko/..." autocomplete="off">
        <button class="btn-go" type="submit">判定する</button>
      </form>
      <button class="demo" id="demoBtn" type="button">▶ サンプル物件で試す（キー設定なしでOK）</button>
      <div class="steps">
        <div class="step"><div class="n">1</div><div class="t">SUUMOのURLを貼る</div></div>
        <div class="step"><div class="n">2</div><div class="t">周辺事例を自動収集</div></div>
        <div class="step"><div class="n">3</div><div class="t">割安度A〜Eで判定</div></div>
      </div>
      <p class="note">※判定は公的取引データに基づく推定値です。実際の価値は個別条件で変動します。
         ※SUUMOの自動取得は同サイト規約の確認が必要です（本デモは学習・検証用）。</p>
    </section>

    <section id="result"></section>
  </main>

  <footer class="site">© VALUE SCAN（学習用プロトタイプ）｜データ出典：国土交通省 不動産情報ライブラリ</footer>

<script>
const form = document.getElementById('form');
const result = document.getElementById('result');
const demoBtn = document.getElementById('demoBtn');
const goBtn = form.querySelector('.btn-go');

function loading(){ result.innerHTML =
  '<div class="res-card"><div class="loading"><div class="spinner"></div>周辺の取引・成約事例を集計しています…</div></div>'; }

function esc(s){ return (s??'').toString().replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }

async function appraise(payload){
  loading(); goBtn.disabled = true;
  try{
    const r = await fetch('/api/appraise', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await r.json();
    render(data);
  }catch(e){
    result.innerHTML = '<div class="res-card"><div class="res-body"><div class="err">通信エラーが発生しました。時間をおいて再度お試しください。</div></div></div>';
  }finally{ goBtn.disabled = false; }
}

function render(d){
  if(!d.ok){
    result.innerHTML = '<div class="res-card"><div class="res-body"><div class="err">⚠️ '+esc(d.message)+'</div></div></div>';
    return;
  }
  const p = d.property, res = d.result;
  const verdict = res.is_cheap
    ? `相場より <b>${esc(res.diff_man)}</b> 割安（▼${res.discount_pct}%）`
    : `相場より <b>${esc(res.diff_man)}</b> 割高（▲${Math.abs(res.discount_pct)}%）`;
  const comps = (d.comps||[]).slice(0,4).map(c=>`
    <div class="comp">
      <div><span class="tag ${c.tag==='成約'?'deal':''}">${c.tag}</span>${esc(c.price_man)}
        <span style="color:#889"> / ${c.area?Math.round(c.area)+'㎡':'—'} ${c.age!=null?'築'+c.age:''} ${esc(c.floor_plan||'')}</span></div>
      <div style="color:#99a;white-space:nowrap">${esc(c.where||'')}</div>
    </div>`).join('');

  result.innerHTML = `
   <div class="res-card">
     <div class="res-head" style="background:${res.grade_color}">
       <div class="pname">${esc(p.name)}</div>
       <div class="grade-row"><div class="grade">${res.grade}</div><div class="grade-label">${esc(res.grade_label)}</div></div>
       <div class="verdict">${verdict}</div>
     </div>
     <div class="res-body">
       <div class="prices">
         <div class="pbox"><div class="l">売出価格</div><div class="v">${esc(res.asking_man)}</div></div>
         <div class="pbox"><div class="l">推定相場</div><div class="v" style="color:${res.grade_color}">${esc(res.estimated_man)}</div></div>
       </div>
       <div class="range">推定レンジ：${esc(res.price_low_man)} 〜 ${esc(res.price_high_man)}（㎡単価 約${esc(res.unit_price_man)}）</div>
       <div class="spec">
         ${p.area_m2?`<span><b>専有面積</b> ${Math.round(p.area_m2)}㎡</span>`:''}
         ${p.floor_plan?`<span><b>間取り</b> ${esc(p.floor_plan)}</span>`:''}
         ${p.age!=null?`<span><b>築年数</b> 築${p.age}年</span>`:''}
         ${p.city?`<span><b>エリア</b> ${esc(p.city)}</span>`:''}
       </div>
       <div class="comps">
         <h3>周辺の取引・成約事例（${res.n_comps}件から推定 / 成約${res.n_deals}件）</h3>
         ${comps}
       </div>
       <div class="meta">判定根拠：${esc(res.method)}・信頼度 ${esc(res.confidence)}</div>
     </div>
     <div class="res-foot">
       ${p.url?`<a href="${esc(p.url)}" target="_blank" rel="noopener">SUUMOで物件を見る →</a><br>`:''}
       推定値です。割安判定が出ても利益を保証するものではありません。データ出典：国土交通省 不動産情報ライブラリ
     </div>
   </div>`;
  result.scrollIntoView({behavior:'smooth', block:'start'});
}

form.addEventListener('submit', e=>{
  e.preventDefault();
  const url = document.getElementById('url').value.trim();
  if(!url){ return; }
  appraise({url});
});
demoBtn.addEventListener('click', ()=> appraise({demo:true}));
</script>
</body>
</html>
'''


"""
ISOGE! クローン — Flaskアプリ（LINE Bot + Web を 1つのバックエンドで提供）

ルート:
  GET  /                 … Web版UI（SUUMO URLを貼り付け）
  POST /api/appraise     … Web版のJSON API（{url} か {demo:true}）
  POST /callback         … LINE Messaging API のWebhook
  GET  /healthz          … 死活監視

環境変数（.env.example 参照）:
  LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN … LINE Bot用
  REINFOLIB_API_KEY                              … 国交省API用
  DEMO_MODE=1                                    … 強制デモ（サンプル事例）

REINFOLIB_API_KEY が未設定のときは自動的にデモモードで動作する
（キー到着前でも Web/LINE の判定動作を確認できる）。
"""


import base64
import hashlib
import hmac
import os

import requests
from flask import Flask, abort, jsonify, render_template, request

# .env があれば読み込む（無くても動く）
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:  # noqa: BLE001
    pass


app = Flask(__name__)

LINE_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
# DEMO_MODE=1 を明示、または 国交省キー未設定なら 自動的にデモ
DEMO_MODE = (os.environ.get("DEMO_MODE") == "1") or not os.environ.get("REINFOLIB_API_KEY")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


# --------------------------------------------------------------------------- #
# Web版
# --------------------------------------------------------------------------- #

@app.get("/")
def index():
    return INDEX_HTML


@app.post("/api/appraise")
def api_appraise():
    payload = request.get_json(silent=True) or {}
    use_mock = DEMO_MODE or bool(payload.get("demo"))

    if payload.get("demo"):
        result = appraise_manual(SAMPLE_PROPERTY, use_mock=True)
    else:
        url = is_suumo_url(payload.get("url", ""))
        if not url:
            return jsonify({"ok": False,
                            "message": "SUUMOの物件URLを入力してください。"}), 400
        result = appraise_from_url(url, use_mock=use_mock)

    return jsonify(_serialize(result))


def _serialize(result: Result) -> dict:
    if not result.ok:
        return {"ok": False, "message": result.message,
                "property": result.prop.to_dict() if result.prop else None}
    ap = result.appraisal
    prop = result.prop
    return {
        "ok": True,
        "demo": result.demo,
        "property": {
            "name": prop.name, "url": prop.url, "address": prop.address,
            "area_m2": prop.area_m2, "floor_plan": prop.floor_plan,
            "built_year": prop.built_year, "age": prop.age,
            "station": prop.station, "city": result.city_name,
        },
        "result": {
            "grade": ap.grade, "grade_label": ap.grade_label, "grade_color": ap.grade_color,
            "asking_price": ap.asking_price, "asking_man": yen_man(ap.asking_price),
            "estimated_price": ap.estimated_price, "estimated_man": yen_man(ap.estimated_price),
            "price_low_man": yen_man(ap.price_low), "price_high_man": yen_man(ap.price_high),
            "diff_man": yen_man(abs(ap.diff_yen)),
            "discount_pct": round(ap.discount_pct, 1),
            "is_cheap": ap.discount_pct >= 0,
            "confidence": ap.confidence, "method": ap.method,
            "n_comps": ap.n_comps, "n_deals": ap.n_deals,
            "unit_price_man": yen_man(int(ap.estimated_unit_price)),
        },
        "comps": [
            {"tag": "成約" if c.is_deal else "取引",
             "price_man": yen_man(c.trade_price),
             "area": c.area, "age": c.age,
             "floor_plan": c.floor_plan,
             "where": c.station or c.district, "period": c.period}
            for c in ap.representative
        ],
    }


# --------------------------------------------------------------------------- #
# LINE Bot Webhook
# --------------------------------------------------------------------------- #

def _verify_signature(body: bytes, signature: str) -> bool:
    if not LINE_SECRET or not signature:
        return False
    mac = hmac.new(LINE_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(mac).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def _reply(reply_token: str, messages: list[dict]) -> None:
    if not LINE_TOKEN:
        app.logger.warning("LINE_CHANNEL_ACCESS_TOKEN 未設定のため返信スキップ")
        return
    requests.post(
        LINE_REPLY_URL,
        headers={"Authorization": f"Bearer {LINE_TOKEN}",
                 "Content-Type": "application/json"},
        json={"replyToken": reply_token, "messages": messages[:5]},
        timeout=15,
    )


@app.post("/callback")
def callback():
    body = request.get_data()
    signature = request.headers.get("X-Line-Signature", "")
    if not _verify_signature(body, signature):
        abort(400)

    data = request.get_json(silent=True) or {}
    for event in data.get("events", []):
        etype = event.get("type")
        reply_token = event.get("replyToken")

        if etype == "follow":
            _reply(reply_token, [{"type": "text", "text": WELCOME_TEXT}])
            continue

        if etype != "message" or event.get("message", {}).get("type") != "text":
            continue

        text = event["message"]["text"]
        url = is_suumo_url(text)
        if not url:
            _reply(reply_token, [{"type": "text", "text": WELCOME_TEXT}])
            continue

        result = appraise_from_url(url, use_mock=DEMO_MODE)
        _reply(reply_token, build_messages(result))

    return "OK"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "demo_mode": DEMO_MODE}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)