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

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Optional

from reinfolib import Comp

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
