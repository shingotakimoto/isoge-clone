from __future__ import annotations
import base64, hashlib, hmac, json, os, math, re, statistics, datetime, urllib.parse
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
不動産物件ページの汎用パーサ（VALUE SCAN）。

許可せず限定もしない：公開URLを送れば解析を試み、価格/面積/所在地/築年/間取り/階 を抽出。
抽出の優先順位:
  1) JSON-LD (application/ld+json) の name/price/floorSize/address
  2) dt/dd・th/td のラベル→値（SUUMO等の表）
  3) ページ全文への正規表現スキャン（フォールバック：各社サイト）

【注意】各サイトの自動取得は各社の利用規約に抵触する可能性があります。本番運用では
各社の許諾・公式データ提供をご確認ください。JavaScript描画ページは取得できません。
"""


import json
import re
from dataclasses import dataclass, asdict

from typing import Optional
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

USER_AGENT = ("Mozilla/5.0 (compatible; value-scan/1.0; appraisal-prototype)")
TIMEOUT = 20

# 既知の不動産サイト（メッセージ表示用。判定はこれに限定しない）
KNOWN_SITES = ["suumo.jp", "homes.co.jp", "athome.co.jp", "realestate.yahoo.co.jp",
               "myhome.nifty.com", "rehouse.co.jp", "livable.co.jp", "stepon.co.jp",
               "nomu.com", "daikyo-anabuki.co.jp"]

_BLOCKED_HOST = re.compile(
    r"^(localhost|0\.0\.0\.0)$|^127\.|^10\.|^192\.168\.|^172\.(1[6-9]|2\d|3[01])\.|"
    r"^169\.254\.|\.local$|^\[?::1\]?$")

PREFECTURES = ("北海道青森県岩手県宮城県秋田県山形県福島県茨城県栃木県群馬県埼玉県千葉県"
               "東京都神奈川県新潟県富山県石川県福井県山梨県長野県岐阜県静岡県愛知県三重県"
               "滋賀県京都府大阪府兵庫県奈良県和歌山県鳥取県島根県岡山県広島県山口県徳島県"
               "香川県愛媛県高知県福岡県佐賀県長崎県熊本県大分県宮崎県鹿児島県沖縄県")
_PREF_LIST = re.findall(r"..[都道府県]", PREFECTURES)
_ADDR_RE = re.compile("(" + "|".join(map(re.escape, _PREF_LIST)) + r")[^\s、，,。]{0,18}?[市区郡]")


class PropertyParseError(RuntimeError):
    pass


@dataclass
class Property:
    name: str
    price_yen: Optional[int]
    address: str
    area_m2: Optional[float]
    floor_plan: str
    built_year: Optional[int]
    built_month: Optional[int]
    floor: Optional[int]
    station: str
    walk_min: Optional[int]
    structure: str
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
# URL 抽出（公開URLのみ・内部/プライベートは拒否）
# --------------------------------------------------------------------------- #

def is_suumo_url(text: str) -> Optional[str]:
    """テキストから最初の公開http(s) URLを返す（内部宛はNone）。互換のため名称据え置き。"""
    m = re.search(r"https?://[^\s]+", text or "")
    if not m:
        return None
    url = m.group().rstrip("　 、。)）」』>")
    host = (urlparse(url).hostname or "").lower()
    if not host or _BLOCKED_HOST.search(host):
        return None
    return url


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    if resp.status_code != 200:
        raise PropertyParseError(f"ページ取得に失敗しました（HTTP {resp.status_code}）")
    resp.encoding = resp.apparent_encoding or resp.encoding or "utf-8"
    return resp.text


# --------------------------------------------------------------------------- #
# 値パーサ
# --------------------------------------------------------------------------- #

def _to_price(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    s = s.replace(",", "").replace(" ", "").replace("　", "")
    total = 0
    mo = re.search(r"(\d+(?:\.\d+)?)億", s)
    if mo:
        total += int(float(mo.group(1)) * 1_0000_0000)
    mm = re.search(r"(\d+(?:\.\d+)?)万", s)
    if mm:
        total += int(float(mm.group(1)) * 1_0000)
    return total or None


def _to_area(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:㎡|m²|m\s*2|m2|平米|平方メートル)", s, re.I)
    return float(m.group(1)) if m else None


def _to_built(s: Optional[str]):
    if not s:
        return None, None
    year = month = None
    m = re.search(r"(19|20)\d{2}", s)
    if m:
        year = int(m.group())
    else:
        year = _to_west_year(s)
    mm = re.search(r"年\s*(\d{1,2})\s*月", s)
    if mm:
        month = int(mm.group(1))
    if year is None:
        ma = re.search(r"築\s*(\d{1,3})\s*年", s)
        if ma:
            year = _dt.now().year - int(ma.group(1))
    return year, month


def _to_floor(s):
    if not s:
        return None
    m = re.search(r"(\d+)\s*階", s)
    return int(m.group(1)) if m else None


def _to_walk(s):
    if not s:
        return None
    m = re.search(r"歩\s*(\d+)\s*分", s) or re.search(r"(\d+)\s*分", s)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------- #
# ① JSON-LD
# --------------------------------------------------------------------------- #

def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _from_jsonld(soup):
    out = {}
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or sc.get_text() or "")
        except Exception:
            continue
        for node in _walk(data):
            if not isinstance(node, dict):
                continue
            if "name" in node and "name" not in out and isinstance(node["name"], str):
                out["name"] = node["name"]
            # price
            for key in ("price",):
                if key in node and "price" not in out:
                    try:
                        out["price"] = int(float(str(node[key]).replace(",", "")))
                    except Exception:
                        pass
            off = node.get("offers")
            if isinstance(off, dict) and "price" not in out and off.get("price"):
                try:
                    out["price"] = int(float(str(off["price"]).replace(",", "")))
                except Exception:
                    pass
            fs = node.get("floorSize")
            if isinstance(fs, dict) and "area" not in out and fs.get("value"):
                try:
                    out["area"] = float(str(fs["value"]).replace(",", ""))
                except Exception:
                    pass
            ad = node.get("address")
            if "address" not in out:
                if isinstance(ad, str):
                    out["address"] = ad
                elif isinstance(ad, dict):
                    out["address"] = "".join(str(ad.get(k, "")) for k in
                                             ("addressRegion", "addressLocality", "streetAddress"))
    return out


# --------------------------------------------------------------------------- #
# ② ラベル表
# --------------------------------------------------------------------------- #

def _label_map(soup):
    pairs = {}
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


def _find(pairs, *keys):
    for label, val in pairs.items():
        if any(k in label for k in keys):
            return val
    return None


# --------------------------------------------------------------------------- #
# ③ 全文スキャン（フォールバック）
# --------------------------------------------------------------------------- #

def _scan_price(text):
    cands = []
    for m in re.finditer(r"(?:(\d+)\s*億)?\s*([0-9,]+)\s*万円", text):
        p = _to_price(m.group(0))
        if p and 3_000_000 <= p <= 3_000_000_000:   # 300万〜30億の範囲
            cands.append(p)
    return max(cands) if cands else None            # 詳細ページでは本体価格が最大になりやすい


def _scan_area(text):
    cands = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:㎡|m²|m\s*2|m2|平米)", text, re.I):
        a = float(m.group(1))
        if 10 <= a <= 400:
            cands.append(a)
    # 専有面積は最頻ではなく「最初の妥当値」を採用しがち。中央値で安定化。
    if not cands:
        return None
    cands.sort()
    return cands[len(cands) // 2]


def _scan_address(text):
    m = _ADDR_RE.search(text)
    return m.group(0) if m else None


def _scan_built(text):
    m = re.search(r"((?:19|20)\d{2})\s*年\s*(\d{1,2})?\s*月?\s*築", text)
    if m:
        return int(m.group(1)), (int(m.group(2)) if m.group(2) else None)
    m = re.search(r"築\s*(\d{1,3})\s*年", text)
    if m:
        return _dt.now().year - int(m.group(1)), None
    return None, None


# --------------------------------------------------------------------------- #
# メイン
# --------------------------------------------------------------------------- #

def parse_property(html: str, url: str = "") -> Property:
    soup = BeautifulSoup(html, "html.parser")
    full = soup.get_text(" ", strip=True)
    pairs = _label_map(soup)
    ld = _from_jsonld(soup)

    # 物件名
    name = ld.get("name") or ""
    if not name:
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            name = og["content"].strip()
    if not name:
        h1 = soup.find("h1")
        name = h1.get_text(strip=True) if h1 else ""
    name = re.sub(r"[｜|【】\[\]].*$", "", name).strip() or "物件"

    price = (ld.get("price")
             or _to_price(_find(pairs, "価格", "販売価格", "物件価格"))
             or _scan_price(full))
    area_label = _find(pairs, "専有面積", "面積")
    area = ld.get("area") or _to_area(area_label)
    if area is None and area_label:
        mnum = re.search(r"(\d+(?:\.\d+)?)", area_label)
        if mnum and 10 <= float(mnum.group(1)) <= 400:
            area = float(mnum.group(1))
    area = area or _scan_area(full)
    address = (_find(pairs, "所在地", "住所", "所在")
               or ld.get("address")
               or _scan_address(full) or "")
    by, bm = _to_built(_find(pairs, "築年月", "完成時期", "竣工", "建築年月", "築年"))
    if not by:
        by, bm = _scan_built(full)
    floor_plan = _find(pairs, "間取り", "間取りタイプ") or ""
    if not floor_plan:
        m = re.search(r"[1-9]\s?[SLDK]{1,3}", full)
        floor_plan = m.group(0).replace(" ", "") if m else ""
    floor = _to_floor(_find(pairs, "所在階", "階数", "向き/階"))
    station = _find(pairs, "沿線・駅", "交通", "最寄", "アクセス") or ""

    prop = Property(name=name[:40], price_yen=price, address=address, area_m2=area,
                    floor_plan=floor_plan, built_year=by, built_month=bm, floor=floor,
                    station=station, walk_min=_to_walk(station), structure="", url=url)

    missing = [n for n, v in (("価格", prop.price_yen), ("専有面積", prop.area_m2),
                              ("所在地", prop.address)) if not v]
    if missing:
        raise PropertyParseError(
            "このページからは " + "・".join(missing) + " を取得できませんでした。"
            "未対応サイトか、JavaScriptで表示されるページの可能性があります。"
            "（対応例：SUUMO / HOME'S / 各仲介会社サイト 等のサーバー表示ページ）")
    return prop


def fetch_property(url: str) -> Property:
    return parse_property(fetch_html(url), url)


# --------------------------------------------------------------------------- #
# 一覧（検索結果）ページの抽出
# --------------------------------------------------------------------------- #

def parse_listing(html: str, base_url: str = "") -> list:
    """検索結果ページから物件サマリを複数抽出（リンク近傍ブロック方式・クラス名非依存）。"""
    soup = BeautifulSoup(html, "html.parser")
    items, seen = [], set()

    # 1) 物件ブロック（dottableを含むカセット）
    for b in soup.select("div.property_unit-content, div.property_unit, div.cassetteitem, .dottable--cassette"):
        a = b.find("a", href=True)
        if not a:
            continue
        txt = b.get_text(" ", strip=True)
        pairs = _label_map(b)
        price = _to_price(_find(pairs, "価格", "販売価格")) or _scan_price(txt)
        area = _to_area(_find(pairs, "専有面積", "面積")) or _scan_area(txt)
        url = urljoin(base_url, a["href"])
        if price and area and url not in seen:
            seen.add(url)
            by, _bm = _scan_built(txt)
            items.append({"name": (a.get_text(strip=True) or "物件")[:40], "url": url,
                          "price_yen": price, "area_m2": area,
                          "address": _scan_address(txt) or "", "built_year": by})
    if items:
        return items

    # 2) 物件詳細リンク（nc_数字 等）の近傍ブロックから抽出
    for a in soup.find_all("a", href=True):
        if not re.search(r"(nc_\d+|bc_\d+|/b-\d+|/bukken/\d|nj_\d+)", a["href"]):
            continue
        cur = a
        for _ in range(6):
            cur = cur.parent
            if cur is None:
                break
            txt = cur.get_text(" ", strip=True)
            if "万円" in txt and re.search(r"\d+(?:\.\d+)?\s*(?:㎡|m²|m\s*2|平米)", txt):
                price = _scan_price(txt)
                area = _scan_area(txt)
                url = urljoin(base_url, a["href"])
                if price and area and url not in seen and len(txt) < 800:
                    seen.add(url)
                    by, _bm = _scan_built(txt)
                    items.append({"name": (a.get_text(strip=True) or "物件")[:40], "url": url,
                                  "price_yen": price, "area_m2": area,
                                  "address": _scan_address(txt) or "", "built_year": by})
                break
    return items


def fetch_listing(url: str) -> list:
    return parse_listing(fetch_html(url), url)

"""
相場推定と割安判定ロジック（VALUE SCAN）。

  1. 同一市区町村の中古マンション事例(Comp)を集める
  2. 外れ値(IQR)除去
  3. 築年で㎡単価を補正して現時点の推定㎡単価を算出
  4. 推定㎡単価 × 専有面積 = 現時点の相場価格
  5. 事例の年次トレンドから年次価格騰落率を求め、1年後の相場を予測
  6. 売出価格 ÷ 相場 → 割安度 S>A>B>C>D>E>F
純Pythonのみ。データ出典は国土交通省の取引・成約価格情報。
"""


import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Optional


MIN_FOR_REGRESSION = 12
MIN_COMPS = 4
TSUBO = 3.305785        # 1坪 = 3.305785 m2


# ---- 統計ヘルパ ----
def _quantile(xs, q):
    if not xs:
        return 0.0
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return s[int(pos)]
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def _iqr_filter(comps):
    prices = [c.unit_price for c in comps]
    if len(prices) < 4:
        return comps
    q1, q3 = _quantile(prices, 0.25), _quantile(prices, 0.75)
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return [c for c in comps if lo <= c.unit_price <= hi]


def _linregress(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b1 = sxy / sxx
    return my - b1 * mx, b1


def depreciation_factor(age):
    if age is None:
        age = 25
    age = max(0, age)
    f = (1.0 - 0.013 * age) if age <= 30 else (1.0 - 0.013 * 30) - 0.004 * (age - 30)
    return max(0.45, min(1.05, f))


def _comp_year(c):
    m = re.search(r"(19|20)\d{2}", c.period or "")
    return int(m.group()) if m else None


def _comp_quarter(c):
    y = _comp_year(c)
    if not y:
        return None
    m = re.search(r"第([1-4])四半期", c.period or "")
    q = int(m.group(1)) if m else 1
    return (y, q)


GRADE_ORDER = ["S", "A", "B", "C", "D", "E", "F"]


def _annual_rate(comps, est_unit):
    """事例の取引年から㎡単価の年次騰落率(小数)を推定。-10%〜+15%でクランプ。"""
    pts = [(y, c.unit_price) for c in comps if (y := _comp_year(c))]
    if len({y for y, _ in pts}) < 2 or len(pts) < 6:
        return 0.0
    reg = _linregress([y for y, _ in pts], [u for _, u in pts])
    if not reg:
        return 0.0
    _, b1 = reg
    base = est_unit or statistics.fmean([u for _, u in pts])
    if not base:
        return 0.0
    return max(-0.10, min(0.15, b1 / base))


# ---- 割安度グレード（売出÷相場：小さいほど割安）----
GRADES = [
    (0.85, "S", "非常に割安", "#16a085"),
    (0.92, "A", "かなり割安", "#1aa260"),
    (0.98, "B", "割安",       "#3ac17a"),
    (1.06, "C", "適正",       "#2b8cd9"),
    (1.14, "D", "やや割高",   "#e8943a"),
    (1.22, "E", "割高",       "#e0663a"),
    (9.99, "F", "かなり割高", "#d9534f"),
]
GRADE_LEGEND = ""
GRADE_COLORS = {g: color for _u, g, _l, color in GRADES}


def _grade_for(ratio):
    for upper, g, label, color in GRADES:
        if ratio <= upper:
            return g, label, color
    return "F", "かなり割高", "#d9534f"


def _confidence(n, cv):
    if n >= 20 and cv <= 0.28:
        return "高"
    if n >= 8 and cv <= 0.45:
        return "中"
    return "低"


def _similar(comps, age, area):
    def near(c):
        if age is not None and c.age is not None and abs(c.age - age) > 15:
            return False
        if area and c.area and not (0.5 * area <= c.area <= 1.6 * area):
            return False
        return True
    narrowed = [c for c in comps if near(c)]
    return narrowed if len(narrowed) >= MIN_COMPS else comps


def _select(comps, district, age, area):
    """建物寄せの段階フィルタ：同地区→近い築年・面積→エリア全体 の順で十分件数の最も狭い層を返す。"""
    def area_ok(c, r):
        return (not area) or (not c.area) or ((1 - r) * area <= c.area <= (1 + r) * area)
    def age_ok(c, d):
        return age is None or c.age is None or abs(c.age - age) <= d
    def dist_ok(c):
        return bool(district) and bool(c.district) and (district in c.district or c.district in district)
    tiers = [
        ("同地区・同築年帯で厳選", lambda c: dist_ok(c) and age_ok(c, 3) and area_ok(c, 0.3)),
        ("同地区で抽出", lambda c: dist_ok(c) and age_ok(c, 8) and area_ok(c, 0.6)),
        ("近い築年・面積で抽出", lambda c: age_ok(c, 10) and area_ok(c, 0.5)),
        ("エリア全体で推定", lambda c: True),
    ]
    for label, f in tiers:
        sel = [c for c in comps if f(c)]
        if len(sel) >= MIN_COMPS:
            return sel, label
    return comps, "エリア全体で推定"


@dataclass
class Appraisal:
    ok: bool
    message: str = ""
    estimated_unit_price: Optional[float] = None   # 現時点 推定㎡単価
    estimated_price: Optional[int] = None          # 現時点 相場（円）
    price_low: Optional[int] = None
    price_high: Optional[int] = None
    asking_price: Optional[int] = None
    asking_unit_price: Optional[float] = None       # 物件㎡単価
    ratio: Optional[float] = None
    diff_yen: Optional[int] = None
    discount_pct: Optional[float] = None
    grade: Optional[str] = None                     # 現時点グレード
    grade_label: str = ""
    grade_color: str = ""
    expected_profit: Optional[int] = None           # 現時点 期待利益(相場−売出)
    annual_rate: float = 0.0                         # 年次価格騰落率(小数)
    future_unit_price: Optional[float] = None        # 1年後 推定㎡単価
    future_price: Optional[int] = None               # 1年後 相場
    future_grade: Optional[str] = None
    future_grade_label: str = ""
    future_grade_color: str = ""
    future_profit: Optional[int] = None              # 1年後 期待利益
    confidence: str = ""
    n_comps: int = 0
    n_deals: int = 0
    method: str = ""
    representative: list = field(default_factory=list)
    yearly: list = field(default_factory=list)
    quarterly: list = field(default_factory=list)
    latest: dict = field(default_factory=dict)


def appraise(area_m2, age, asking_price, comps, district=None):
    if not area_m2 or not asking_price:
        return Appraisal(ok=False, message="専有面積または売出価格が不明です。")

    comps = [c for c in comps if c.unit_price and c.unit_price > 0]
    n_deals = sum(1 for c in comps if c.is_deal)
    comps = _iqr_filter(comps)
    if len(comps) < MIN_COMPS:
        return Appraisal(ok=False, n_comps=len(comps), n_deals=n_deals,
                         message=("周辺の取引事例が不足しているため判定できませんでした"
                                  f"（有効事例 {len(comps)} 件）。"))

    used, tier = _select(comps, district, age, area_m2)
    unit_prices = [c.unit_price for c in used]
    mean_up = statistics.fmean(unit_prices)
    cv = (statistics.pstdev(unit_prices) / mean_up) if mean_up else 1.0

    # 現時点の推定㎡単価
    est_unit, method = None, ""
    aged = [(c.age, c.unit_price) for c in used if c.age is not None]
    if len(aged) >= MIN_FOR_REGRESSION and age is not None:
        reg = _linregress([a for a, _ in aged], [u for _, u in aged])
        if reg:
            b0, b1 = reg
            pred = b0 + b1 * age
            lo = _quantile([u for _, u in aged], 0.05)
            hi = _quantile([u for _, u in aged], 0.95)
            if b1 <= 0 and lo <= pred <= hi:
                est_unit, method = pred, f"{tier}・築年回帰（{len(aged)}件）"
    if est_unit is None:
        med_up = statistics.median(unit_prices)
        ages = [c.age for c in used if c.age is not None]
        base_age = statistics.median(ages) if ages else 25
        est_unit = med_up * (depreciation_factor(age) / depreciation_factor(int(base_age)))
        method = f"{tier}・中央値補正（{len(used)}件）"

    estimated_price = int(est_unit * area_m2)
    ratio = asking_price / estimated_price
    grade, label, color = _grade_for(ratio)
    band = max(0.08, min(0.25, cv * 0.8))

    # 年次騰落率 → 1年後予測
    rate = _annual_rate(comps, est_unit)
    future_unit = est_unit * (1 + rate)
    future_price = int(future_unit * area_m2)
    fratio = asking_price / future_price
    fgrade, flabel, fcolor = _grade_for(fratio)

    def sim_key(c):
        return (0 if c.is_deal else 1, abs((c.age or 999) - (age or 0)),
                abs((c.area or 0) - area_m2))
    representative = sorted(used, key=sim_key)[:5]

    # 年別集計（チャート用）: 取引年ごとの市場価格(万円)と流通戸数
    ybuckets = {}
    for c in comps:
        y = _comp_year(c)
        if y:
            ybuckets.setdefault(y, []).append(c.unit_price)
    yearly = [{"year": y, "market_man": round(statistics.fmean(v) * area_m2 / 1_0000),
               "count": len(v)} for y, v in sorted(ybuckets.items())]

    # 四半期集計（直近20四半期＝5年）: 市場価格(万円)/流通戸数/成約戸数
    qb = {}
    for c in comps:
        qk = _comp_quarter(c)
        if not qk:
            continue
        d = qb.setdefault(qk, {"ups": [], "flow": 0, "deal": 0})
        d["ups"].append(c.unit_price)
        d["flow"] += 1
        if c.is_deal:
            d["deal"] += 1
    quarterly = []
    for (y, q) in sorted(qb)[-20:]:
        d = qb[(y, q)]
        quarterly.append({"label": f"{y}/Q{q}",
                          "market_man": round(statistics.fmean(d["ups"]) * area_m2 / 1_0000),
                          "flow": d["flow"], "deal": d["deal"]})

    # 直近の成約事例（成約優先・最新の四半期）
    def rec_key(c):
        qk = _comp_quarter(c) or (0, 0)
        return (1 if c.is_deal else 0, qk[0], qk[1])
    latest = {}
    if comps:
        lc = max(comps, key=rec_key)
        latest = {"period": lc.period, "floor_plan": lc.floor_plan,
                  "trade_price": lc.trade_price, "area": lc.area,
                  "unit_price": lc.unit_price, "is_deal": lc.is_deal}

    return Appraisal(
        ok=True,
        estimated_unit_price=est_unit, estimated_price=estimated_price,
        price_low=int(estimated_price * (1 - band)),
        price_high=int(estimated_price * (1 + band)),
        asking_price=asking_price, asking_unit_price=asking_price / area_m2,
        ratio=ratio, diff_yen=asking_price - estimated_price,
        discount_pct=(1 - ratio) * 100,
        grade=grade, grade_label=label, grade_color=color,
        expected_profit=estimated_price - asking_price,
        annual_rate=rate,
        future_unit_price=future_unit, future_price=future_price,
        future_grade=fgrade, future_grade_label=flabel, future_grade_color=fcolor,
        future_profit=future_price - asking_price,
        confidence=_confidence(len(used), cv),
        n_comps=len(comps), n_deals=n_deals, method=method,
        representative=representative,
        yearly=yearly,
        quarterly=quarterly,
        latest=latest,
    )


# ---- 表示用 ----
def yen_man(yen):
    if yen is None:
        return "—"
    man = round(yen / 1_0000)
    if man >= 1_0000:
        oku, rest = divmod(man, 1_0000)
        return f"{oku}億{rest:,}万円" if rest else f"{oku}億円"
    return f"{man:,}万円"


def tsubo_man(unit_price_m2):
    """㎡単価(円) → 坪単価表示「○○万円」"""
    if not unit_price_m2:
        return "—"
    return yen_man(int(unit_price_m2 * TSUBO))


def profit_str(yen):
    """期待利益：+○○万円 / ▲○○万円"""
    if yen is None:
        return "—"
    man = round(abs(yen) / 1_0000)
    return f"+{man:,}万円" if yen >= 0 else f"▲{man:,}万円"

from dataclasses import dataclass
from typing import Optional

SAMPLE_PROPERTY = Property(
    name="サンプルレジデンス豊洲（デモ）", price_yen=52_800_000,
    address="東京都江東区豊洲4丁目", area_m2=68.0, floor_plan="3LDK",
    built_year=2009, built_month=3, floor=12,
    station="東京メトロ有楽町線 豊洲駅 徒歩8分", walk_min=8, structure="ＲＣ",
    url="https://suumo.jp/ms/chuko/")

def _district_of(address):
    """住所から地区名（丁目・番地を除いた町名）を抽出。例 東京都文京区小石川3丁目 → 小石川"""
    try:
        _, rest = split_prefecture(address or "")
    except Exception:
        rest = address or ""
    rest = re.sub(r"^.+?[区市町村]", "", rest or "", count=1)
    d = re.split(r"[0-9０-９]", rest)[0] if rest else ""
    return d.replace("丁目", "").strip("　 ") or None


@dataclass
class Result:
    ok: bool
    message: str = ""
    prop: Optional[Property] = None
    appraisal: Optional[Appraisal] = None
    city_name: Optional[str] = None
    demo: bool = False

def appraise_from_url(url, use_mock=False):
    # デモでも解析失敗時はサンプルに逃げず「未対応」を正直に返す
    try:
        prop = fetch_property(url)
    except PropertyParseError as e:
        return Result(ok=False, message=str(e))
    except Exception as e:
        return Result(ok=False, message=f"ページ取得エラー: {e}")
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
    ap = appraise(prop.area_m2, prop.age, prop.price_yen, comps,
                            district=_district_of(prop.address))
    if not ap.ok:
        return Result(ok=False, prop=prop, city_name=city_name, appraisal=ap, message=ap.message, demo=demo)
    return Result(ok=True, prop=prop, appraisal=ap, city_name=city_name, demo=demo)


def screen_listing(url, use_mock=False, limit=30):
    """検索結果ページ→各物件を判定→割安順（Sが上）に集計。"""
    try:
        items = fetch_listing(url)
    except PropertyParseError as e:
        return {"ok": False, "message": str(e)}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "message": f"一覧ページ取得エラー: {e}"}
    if not items:
        return {"ok": False, "message": "このページから物件一覧を抽出できませんでした"
                "（未対応/JS描画の可能性）。SUUMOの一覧ページでお試しください。"}

    comps_cache = {}
    results = []
    for it in items[:limit]:
        prop = Property(name=it["name"], price_yen=it["price_yen"], address=it["address"],
                              area_m2=it["area_m2"], floor_plan="", built_year=it["built_year"],
                              built_month=None, floor=None, station="", walk_min=None,
                              structure="", url=it["url"])
        if use_mock:
            comps = fetch_comps("00000", use_mock=True)
        else:
            try:
                _, city_code, _cn = resolve_city_code(prop.address)
            except ReinfolibError:
                continue
            if not city_code:
                continue
            if city_code not in comps_cache:
                comps_cache[city_code] = fetch_comps(city_code)
            comps = comps_cache[city_code]
        ap = appraise(prop.area_m2, prop.age, prop.price_yen, comps,
                                district=_district_of(prop.address))
        if not ap.ok:
            continue
        results.append({"name": prop.name, "url": prop.url, "grade": ap.grade,
                        "grade_label": ap.grade_label, "grade_color": ap.grade_color,
                        "price_man": yen_man(ap.asking_price),
                        "market_man": yen_man(ap.estimated_price),
                        "discount_pct": round(ap.discount_pct, 1), "ratio": ap.ratio,
                        "area": prop.area_m2, "built_year": prop.built_year})
    results.sort(key=lambda r: r["ratio"])
    return {"ok": True, "scanned": len(items), "judged": len(results),
            "s_count": sum(1 for r in results if r["grade"] == "S"), "results": results}


def batch_judge(urls, use_mock=False, limit=30):
    """複数の物件URLを判定→割安順（Sが上）に集計。詳細ページ方式で確実。"""
    results = []
    for u in urls[:limit]:
        r = appraise_from_url(u, use_mock=use_mock)
        if not r.ok:
            continue
        ap, p = r.appraisal, r.prop
        results.append({"name": p.name, "url": p.url, "grade": ap.grade,
                        "grade_label": ap.grade_label, "grade_color": ap.grade_color,
                        "price_man": yen_man(ap.asking_price),
                        "market_man": yen_man(ap.estimated_price),
                        "discount_pct": round(ap.discount_pct, 1), "ratio": ap.ratio,
                        "area": p.area_m2, "built_year": p.built_year})
    results.sort(key=lambda r: r["ratio"])
    return {"ok": True, "judged": len(results),
            "s_count": sum(1 for r in results if r["grade"] == "S"), "results": results}

"""LINE返信（VALUE SCAN）: クリーンな割安判定カード(Flex) ＋ 四半期チャート。"""
import json
import urllib.parse

# 国交省API利用規約で必須のクレジット
MLIT_CREDIT = ("このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、"
               "提供情報の最新性、正確性、完全性等が保証されたものではありません。")


def _row(label, value, bold=False, vcolor="#222222", vsize="sm"):
    return {"type": "box", "layout": "baseline", "spacing": "sm", "contents": [
        {"type": "text", "text": label, "size": "sm", "color": "#888888", "flex": 4},
        {"type": "text", "text": value, "size": vsize, "color": vcolor, "flex": 6,
         "align": "end", "weight": "bold" if bold else "regular", "wrap": True}]}


def build_result_flex(result):
    ap = result.appraisal
    p = result.prop
    name = (p.name if p else "物件")[:40]

    profit = ap.expected_profit or 0
    if profit >= 0:
        diff_text = f"相場より {yen_man(abs(profit))} 割安（▼{ap.discount_pct:.0f}%）"
        diff_color, diff_bg = "#1aa260", "#f3faf5"
    else:
        diff_text = f"相場より {yen_man(abs(profit))} 割高（▲{abs(ap.discount_pct):.0f}%）"
        diff_color, diff_bg = "#d9534f", "#fdf2f2"

    header = {"type": "box", "layout": "vertical", "backgroundColor": ap.grade_color,
              "paddingAll": "16px", "spacing": "xs", "contents": [
                  {"type": "text", "text": "VALUE SCAN 割安度判定", "color": "#ffffffcc", "size": "xs"},
                  {"type": "text", "text": name, "color": "#ffffff", "size": "md",
                   "weight": "bold", "wrap": True},
                  {"type": "box", "layout": "baseline", "spacing": "md", "margin": "md", "contents": [
                      {"type": "text", "text": ap.grade or "?", "color": "#ffffff",
                       "size": "4xl", "weight": "bold", "flex": 0},
                      {"type": "text", "text": ap.grade_label, "color": "#ffffff",
                       "size": "lg", "weight": "bold", "gravity": "center"}]}]}

    body = [
        _row("売出価格", yen_man(ap.asking_price), bold=True, vsize="md"),
        _row("推定相場", yen_man(ap.estimated_price), bold=True, vsize="md"),
        _row("推定レンジ", f"{yen_man(ap.price_low)}〜{yen_man(ap.price_high)}"),
        {"type": "box", "layout": "vertical", "margin": "md", "paddingAll": "10px",
         "backgroundColor": diff_bg, "cornerRadius": "8px", "contents": [
             {"type": "text", "text": diff_text, "size": "sm", "weight": "bold",
              "color": diff_color, "align": "center", "wrap": True}]},
        {"type": "separator", "margin": "lg"},
        _row("1年後の予測相場", f"{yen_man(ap.future_price)}（{ap.future_grade}）"),
        _row("年間騰落率", f"{ap.annual_rate * 100:+.1f}%"),
        {"type": "separator", "margin": "lg"},
    ]
    if p and p.area_m2:
        body.append(_row("専有面積", f"{p.area_m2:.0f}㎡"))
    if p and p.floor_plan:
        body.append(_row("間取り", p.floor_plan))
    body.append(_row("坪単価", tsubo_man(ap.asking_unit_price)))
    if p and p.age is not None:
        body.append(_row("築年数", f"築{p.age}年（{p.built_year}年）"))
    if result.city_name:
        body.append(_row("エリア", result.city_name))
    body.append({"type": "separator", "margin": "lg"})
    body.append({"type": "text", "text": f"周辺の取引・成約事例（{ap.n_comps}件中）",
                 "size": "sm", "weight": "bold", "color": "#2b8cd9", "margin": "md"})
    for c in ap.representative[:3]:
        tag = "成約" if c.is_deal else "取引"
        area = f"{c.area:.0f}㎡" if c.area else "—"
        age = f"築{c.age}" if c.age is not None else ""
        body.append({"type": "text",
                     "text": f"[{tag}] {yen_man(c.trade_price)} / {area} {age} / {c.station or c.district}",
                     "size": "xs", "color": "#555555", "wrap": True, "margin": "sm"})
    body.append({"type": "text", "text": f"判定根拠: {ap.method}・信頼度 {ap.confidence}",
                 "size": "xxs", "color": "#aaaaaa", "margin": "md", "wrap": True})

    footer_contents = []
    if p and p.url:
        footer_contents.append({"type": "button", "style": "primary", "height": "sm",
                                "color": ap.grade_color,
                                "action": {"type": "uri", "label": "物件ページを見る", "uri": p.url}})
    footer_contents.append({"type": "text",
                            "text": "推定値です。実際の価値は個別条件で変動します。",
                            "size": "xxs", "color": "#aaaaaa", "wrap": True, "margin": "sm"})
    footer = {"type": "box", "layout": "vertical", "paddingAll": "12px",
              "spacing": "sm", "contents": footer_contents}

    bubble = {"type": "bubble", "size": "mega",
              "header": header,
              "body": {"type": "box", "layout": "vertical", "paddingAll": "16px",
                       "spacing": "sm", "contents": body},
              "footer": footer}
    return {"type": "flex",
            "altText": f"{name} の割安度判定：{ap.grade}（{ap.grade_label}）",
            "contents": bubble}


def _chart_cfg(ap, quarters, lite=False):
    q = ap.quarterly[-quarters:]
    labels = [d["label"] for d in q]
    market = [d["market_man"] for d in q]
    flow = [d["flow"] for d in q]
    deal = [d["deal"] for d in q]
    asking = round((ap.asking_price or 0) / 1_0000)
    ds = [
        {"type": "line", "label": ("当該価格" if lite else "当該物件価格"),
         "data": [asking] * len(labels), "borderColor": "rgb(20,40,120)",
         "borderDash": [6, 4], "fill": False, "pointRadius": 0, "yAxisID": "R"},
        {"type": "line", "label": ("成約相場" if lite else "成約相場(所在階)"),
         "data": market, "borderColor": "rgb(30,90,230)", "fill": False, "yAxisID": "R"},
        {"type": "bar", "label": ("流通" if lite else "流通戸数"), "data": flow,
         "backgroundColor": "rgba(40,200,170,0.8)", "yAxisID": "L"},
    ]
    if not lite:
        ds.append({"type": "bar", "label": "成約戸数", "data": deal,
                   "backgroundColor": "rgba(20,90,50,0.85)", "yAxisID": "L"})
    title = "価格推移(四半期)" if lite else "物件価格 過去推移 (四半期)"
    return {"type": "bar", "data": {"labels": labels, "datasets": ds},
            "options": {"title": {"display": True, "text": title},
                        "scales": {"yAxes": [
                            {"id": "L", "position": "left",
                             "scaleLabel": {"display": True, "labelString": "戸数"}},
                            {"id": "R", "position": "right",
                             "gridLines": {"drawOnChartArea": False},
                             "scaleLabel": {"display": True, "labelString": "万円"}}]}}}


def chart_url(ap):
    ql = getattr(ap, "quarterly", None)
    if not ql or len(ql) < 2:
        return None
    try:
        r = requests.post("https://quickchart.io/chart/create",
                          json={"chart": _chart_cfg(ap, 16, lite=False),
                                "width": 700, "height": 400, "backgroundColor": "white"},
                          timeout=6)
        if r.ok:
            j = r.json()
            if j.get("success") and j.get("url"):
                return j["url"]
    except Exception:
        pass
    for keep in (10, 8, 6, 4):
        c = json.dumps(_chart_cfg(ap, keep, lite=True), ensure_ascii=False, separators=(",", ":"))
        url = "https://quickchart.io/chart?w=700&h=400&bkg=white&c=" + urllib.parse.quote(c)
        if len(url) <= 1900:
            return url
    return None


def year_chart_url(ap):
    return chart_url(ap)


def build_messages(result):
    if not result.ok:
        return [{"type": "text", "text": "⚠️ " + (result.message or "判定できませんでした。")}]
    msgs = [build_result_flex(result)]
    url = chart_url(result.appraisal)
    if url:
        msgs.append({"type": "image", "originalContentUrl": url, "previewImageUrl": url})
    return msgs


WELCOME_TEXT = (
    "はじめまして！VALUE SCANです。\n"
    "友だち追加ありがとうございます😊\n\n"
    "気になる中古マンションの物件ページURL（SUUMO・HOME'S 等）を送ってください！\n"
    "10秒程度で割安/割高の判定結果をお返しします。\n"
    "もし結果が返ってこない場合は、お手数ですが再送ください。\n\n"
    "※" + MLIT_CREDIT
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
  .srow{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--line)}
  .srow b{white-space:nowrap}
  footer.site{text-align:center;color:var(--muted);font-size:11px;padding:24px}
</style>
</head>
<body>
  <header class="hero">
    <div class="logo">🏢 VALUE SCAN</div>
    <h1>マンション割安判定サービス</h1>
    <div class="en">VALUE SCAN</div>
    <p>気になる中古マンションの <b>物件ページのURLを貼るだけ</b>。<br>
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
      <p class="sub">中古マンションの物件ページURLを貼り付けてください（SUUMO・HOME'S・各仲介会社サイト等）。</p>
      <form id="form" class="field">
        <input id="url" type="url" placeholder="物件ページのURL（SUUMO・HOME'S 等）" autocomplete="off">
        <button class="btn-go" type="submit">判定する</button>
      </form>
      <button class="demo" id="demoBtn" type="button">▶ サンプル物件で試す（キー設定なしでOK）</button>
      <div class="steps">
        <div class="step"><div class="n">1</div><div class="t">SUUMOのURLを貼る</div></div>
        <div class="step"><div class="n">2</div><div class="t">周辺事例を自動収集</div></div>
        <div class="step"><div class="n">3</div><div class="t">割安度A〜Eで判定</div></div>
      </div>
      <p class="note">※判定は公的取引データに基づく推定値です。実際の価値は個別条件で変動します。
         ※各サイトの自動取得は各社規約の確認が必要です（学習・検証用）。</p>
    </section>

    <section id="result"></section>

    <section class="card" style="margin-top:18px">
      <h2>まとめて判定（Sランク抽出）</h2>
      <p class="sub"><b>方法1（確実・推奨）</b>：気になる物件の詳細URLを改行で複数貼り付け</p>
      <form id="bform">
        <textarea id="burls" rows="4" placeholder="https://suumo.jp/ms/chuko/.../nc_xxxxxxxx/  （改行で複数）" style="width:100%;box-sizing:border-box;padding:12px;border:1.5px solid var(--line);border-radius:10px;font-size:13px;outline:none"></textarea>
        <button class="btn-go" type="submit" style="margin-top:8px">URLをまとめて判定</button>
      </form>
      <p class="sub" style="margin-top:16px"><b>方法2（試験的）</b>：SUUMO検索結果ページのURL（サイトにより取得できないことがあります）</p>
      <form id="sform" class="field">
        <input id="surl" type="url" placeholder="検索結果ページのURL（SUUMO）" autocomplete="off">
        <button class="btn-go" type="submit">一覧から判定</button>
      </form>
      <label style="font-size:12px;color:var(--muted);display:inline-block;margin-top:10px"><input type="checkbox" id="sonly"> Sランクのみ表示</label>
      <div id="sresult"></div>
      <p class="note">※物件を順に判定します（最大30件・件数により時間がかかります）。ページ取得は各サイトの規約をご確認ください。実判定には国交省キーが必要です。</p>
    </section>

    <section class="card" style="margin-top:18px">
      <h2>対応サイト（目安）</h2>
      <p class="sub">物件ページのURLを送ると判定します。取得可否はページ構造により変わります。</p>
      <div style="font-size:14px">
        <div class="srow"><span>SUUMO</span><b style="color:#1aa260">✅ 対応</b></div>
        <div class="srow"><span>LIFULL HOME'S</span><b style="color:#1aa260">✅ 対応</b></div>
        <div class="srow"><span>各仲介会社サイト<br><span style="color:#889;font-size:12px">三井のリハウス/東急リバブル/住友不動産販売/ノムコム/三菱地所ハウスネット/東京建物/大京穴吹 ほか</span></span><b style="color:#e8943a">△ ページにより対応</b></div>
        <div class="srow"><span>ニフティ不動産</span><b style="color:#e8943a">△ 要確認</b></div>
        <div class="srow"><span>at home</span><b style="color:#e8943a">△ 取得制限が強く不可が多い</b></div>
        <div class="srow"><span>Yahoo!不動産</span><b style="color:#d9534f">❌ 未対応（JS描画）</b></div>
      </div>
      <p class="note">※ JavaScriptで表示されるサイト（Yahoo!不動産等）やアクセス制限の強いサイトは取得できません。取得できない場合は、SUUMO や HOME'S のURLをお試しください。</p>
    </section>
  </main>

  <footer class="site">© VALUE SCAN（学習用プロトタイプ）<br>このサービスは、国土交通省不動産情報ライブラリのAPI機能を使用していますが、提供情報の最新性・正確性・完全性等が保証されたものではありません。</footer>

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
       ${d.chart_url?`<img src="${esc(d.chart_url)}" alt="年別 市場価格と流通戸数" style="width:100%;margin-top:14px;border:1px solid var(--line);border-radius:8px">`:''}
     </div>
     <div class="res-foot">
       ${p.url?`<a href="${esc(p.url)}" target="_blank" rel="noopener">SUUMOで物件を見る →</a><br>`:''}
       推定値です。割安判定が出ても利益を保証するものではありません。
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

const sform=document.getElementById('sform');
const sresult=document.getElementById('sresult');
const sonly=document.getElementById('sonly');
let _sdata=null;
function thisYear(){return new Date().getFullYear();}
function srender(){
  if(!_sdata){sresult.innerHTML='';return;}
  if(!_sdata.ok){sresult.innerHTML='<div class="err" style="margin-top:10px">\u26a0\ufe0f '+esc(_sdata.message)+'</div>';return;}
  let rows=_sdata.results||[];
  if(sonly.checked) rows=rows.filter(r=>r.grade==='S');
  const head='<div class="sub" style="margin:12px 0 6px">判定 '+_sdata.judged+'件 ／ Sランク '+_sdata.s_count+'件（割安順）</div>';
  if(!rows.length){sresult.innerHTML=head+'<p class="sub">該当物件がありません。</p>';return;}
  sresult.innerHTML=head+rows.map(r=>`
    <div class="srow" style="align-items:flex-start">
      <div style="flex:1">
        <div><b style="color:${r.grade_color};font-size:16px">${r.grade}</b> <span style="font-size:13px">${esc(r.name)}</span></div>
        <div style="font-size:12px;color:#889">売出 ${esc(r.price_man)} / 推定 ${esc(r.market_man)} / ${r.discount_pct>=0?'\u25bc'+r.discount_pct:'\u25b2'+Math.abs(r.discount_pct)}% ${r.area?'/ '+Math.round(r.area)+'\u33a1':''} ${r.built_year?'/ 築'+(thisYear()-r.built_year)+'年':''}</div>
      </div>
      ${r.url?`<a href="${esc(r.url)}" target="_blank" rel="noopener" style="font-size:12px;white-space:nowrap">見る</a>`:''}
    </div>`).join('');
}
if(sform){
  sform.addEventListener('submit', async e=>{
    e.preventDefault();
    const url=document.getElementById('surl').value.trim(); if(!url) return;
    sresult.innerHTML='<div class="loading"><div class="spinner"></div>一覧を判定しています…</div>';
    try{
      const r=await fetch('/api/screen',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
      _sdata=await r.json(); srender();
    }catch(err){ sresult.innerHTML='<div class="err">通信エラーが発生しました。</div>'; }
  });
  sonly.addEventListener('change', srender);
}

const bform=document.getElementById('bform');
if(bform){
  bform.addEventListener('submit', async e=>{
    e.preventDefault();
    const urls=document.getElementById('burls').value.trim(); if(!urls) return;
    sresult.innerHTML='<div class="loading"><div class="spinner"></div>URLをまとめて判定しています…</div>';
    try{
      const r=await fetch('/api/batch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({urls})});
      _sdata=await r.json(); srender();
    }catch(err){ sresult.innerHTML='<div class="err">通信エラーが発生しました。</div>'; }
  });
}
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
        "chart_url": year_chart_url(ap),
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


@app.post("/api/screen")
def api_screen():
    payload = request.get_json(silent=True) or {}
    url = is_suumo_url(payload.get("url", ""))
    if not url:
        return jsonify({"ok": False, "message": "一覧ページのURLを入力してください。"}), 400
    return jsonify(screen_listing(url, use_mock=DEMO_MODE))


@app.post("/api/batch")
def api_batch():
    payload = request.get_json(silent=True) or {}
    urls = []
    for tok in re.split(r"\s+", payload.get("urls", "") or ""):
        u = is_suumo_url(tok)
        if u:
            urls.append(u)
    if not urls:
        return jsonify({"ok": False, "message": "物件URLを1件以上（改行区切りで）入力してください。"}), 400
    return jsonify(batch_judge(urls, use_mock=DEMO_MODE))


@app.get("/healthz")
def healthz():
    return {"status": "ok", "demo_mode": DEMO_MODE}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)