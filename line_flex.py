"""
コマンドラインで割安判定を試すツール（LINE/Web無しでロジックを検証できる）。

例:
  python cli.py --demo
  python cli.py --url "https://suumo.jp/ms/chuko/tokyo/sc_xxx/nc_xxxxxxxxx/"
  python cli.py --manual --address "東京都江東区豊洲4" --area 68 --age 16 --price 68000000 --mock
"""

from __future__ import annotations

import argparse

import service
from appraisal import yen_man
from suumo import Property


def render_text(result: service.Result) -> str:
    if not result.ok:
        return f"判定不可: {result.message}"
    ap, p = result.appraisal, result.prop
    lines = [
        "=" * 48,
        f" {p.name}",
        "=" * 48,
        f" 割安度       : {ap.grade}（{ap.grade_label}）　信頼度 {ap.confidence}",
        f" 売出価格     : {yen_man(ap.asking_price)}",
        f" 推定相場     : {yen_man(ap.estimated_price)}  （{yen_man(ap.price_low)}〜{yen_man(ap.price_high)}）",
        f" 推定㎡単価   : {yen_man(int(ap.estimated_unit_price))}",
    ]
    if ap.discount_pct >= 0:
        lines.append(f" 判定         : 相場より {yen_man(abs(ap.diff_yen))} 割安（▼{ap.discount_pct:.0f}%）")
    else:
        lines.append(f" 判定         : 相場より {yen_man(abs(ap.diff_yen))} 割高（▲{abs(ap.discount_pct):.0f}%）")
    lines += [
        f" 物件         : {p.area_m2:.0f}㎡ / {p.floor_plan} / 築{p.age}年 / {result.city_name or p.address}",
        f" 根拠         : {ap.method}（事例{ap.n_comps}件・うち成約{ap.n_deals}件）",
        "-" * 48,
        " 代表的な取引・成約事例:",
    ]
    for c in ap.representative:
        tag = "成約" if c.is_deal else "取引"
        lines.append(f"  [{tag}] {yen_man(c.trade_price)} / "
                     f"{c.area:.0f}㎡ / 築{c.age if c.age is not None else '?'} / "
                     f"{c.station or c.district} / {c.period}")
    lines.append("=" * 48)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", help="SUUMOの物件URL")
    ap.add_argument("--demo", action="store_true", help="サンプル物件＋サンプル事例で実行")
    ap.add_argument("--manual", action="store_true", help="物件情報を手入力で指定")
    ap.add_argument("--mock", action="store_true", help="国交省APIの代わりにサンプル事例を使う")
    ap.add_argument("--address", default="東京都江東区豊洲4丁目")
    ap.add_argument("--area", type=float, default=68.0)
    ap.add_argument("--age", type=int, default=16)
    ap.add_argument("--price", type=int, default=68_000_000)
    ap.add_argument("--plan", default="3LDK")
    ap.add_argument("--name", default="（手入力物件）")
    args = ap.parse_args()

    if args.demo:
        from service import SAMPLE_PROPERTY
        result = service.appraise_manual(SAMPLE_PROPERTY, use_mock=True)
    elif args.url:
        result = service.appraise_from_url(args.url, use_mock=args.mock)
    elif args.manual:
        import datetime
        prop = Property(
            name=args.name, price_yen=args.price, address=args.address,
            area_m2=args.area, floor_plan=args.plan,
            built_year=datetime.datetime.now().year - args.age, built_month=1,
            floor=None, station="", walk_min=None, structure="ＲＣ", url="",
        )
        result = service.appraise_manual(prop, use_mock=args.mock)
    else:
        ap.print_help()
        return

    print(render_text(result))


if __name__ == "__main__":
    main()
