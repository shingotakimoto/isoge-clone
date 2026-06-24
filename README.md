"""
LINE Flex Message（割安判定カード）の組み立て。
service.Result から LINE の messages 配列を作る。
"""

from __future__ import annotations

from appraisal import yen_man
from service import Result


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
            {"type": "text", "text": "ISOGE! 割安度判定", "color": "#ffffffcc", "size": "xs"},
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
    "ISOGE!クローンへようこそ🏢\n\n"
    "気になる中古マンションの【SUUMOのURL】をそのまま送ってください。\n"
    "周辺の取引・成約事例から、割安/割高度を判定します。\n\n"
    "※判定は推定値です。データ出典: 国土交通省 不動産情報ライブラリ"
)
