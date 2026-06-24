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

from __future__ import annotations

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

import line_flex
import service
from appraisal import yen_man
from service import SAMPLE_PROPERTY
from suumo import is_suumo_url

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
    return render_template("index.html", demo_mode=DEMO_MODE)


@app.post("/api/appraise")
def api_appraise():
    payload = request.get_json(silent=True) or {}
    use_mock = DEMO_MODE or bool(payload.get("demo"))

    if payload.get("demo"):
        result = service.appraise_manual(SAMPLE_PROPERTY, use_mock=True)
    else:
        url = is_suumo_url(payload.get("url", ""))
        if not url:
            return jsonify({"ok": False,
                            "message": "SUUMOの物件URLを入力してください。"}), 400
        result = service.appraise_from_url(url, use_mock=use_mock)

    return jsonify(_serialize(result))


def _serialize(result: service.Result) -> dict:
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
            _reply(reply_token, [{"type": "text", "text": line_flex.WELCOME_TEXT}])
            continue

        if etype != "message" or event.get("message", {}).get("type") != "text":
            continue

        text = event["message"]["text"]
        url = is_suumo_url(text)
        if not url:
            _reply(reply_token, [{"type": "text", "text": line_flex.WELCOME_TEXT}])
            continue

        result = service.appraise_from_url(url, use_mock=DEMO_MODE)
        _reply(reply_token, line_flex.build_messages(result))

    return "OK"


@app.get("/healthz")
def healthz():
    return {"status": "ok", "demo_mode": DEMO_MODE}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
