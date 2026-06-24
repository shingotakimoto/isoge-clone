# デプロイ手順（Render｜無料・公開URLでWeb＋LINE）

このとおり進めると、**インターネット上の公開URL**でWebページとLINE Botの両方が動きます。
最初は **デモモード（サンプル事例）** で起動するので、国交省APIキーが届く前でも判定の動作を確認できます。
キーが届いたら環境変数を1つ変えるだけで実データに切り替わります。

所要時間の目安：15〜20分。必要なアカウントは **GitHub** と **Render**（どちらも無料）。

---

## 全体像

```
あなたのコード（GitHub）──→ Render（Webサービス）──→ 公開URL https://xxxx.onrender.com
                                                        ├─ /            … Web版ページ
                                                        └─ /callback    … LINEのWebhook
```

---

## ステップ1：GitHubにコードを置く（コマンド不要）

1. [github.com](https://github.com/) でアカウントを作成（無料）してログイン。
2. 右上の「＋」→ **New repository**。
   - Repository name: `isoge-clone`（任意）
   - **Public** のままでOK → **Create repository**。
3. 次の画面で **「uploading an existing file」** のリンクをクリック。
4. zipを解凍した **`isoge-line-bot` フォルダの中身**（`app.py` などのファイルと `templates` フォルダ）を、
   ブラウザにドラッグ＆ドロップでアップロード。
   - ※ `isoge-line-bot` フォルダごとではなく、**中身**を入れてください
     （`app.py` がリポジトリ直下に来るように）。
5. 下の **Commit changes** を押す。

> Gitに不慣れでも、この「ファイルをドラッグしてCommit」だけで大丈夫です。

---

## ステップ2：Renderでデプロイ

1. [render.com](https://render.com/) で **GitHubアカウントでサインアップ**。
2. ダッシュボード右上 **New +** → **Blueprint**。
3. さきほどの `isoge-clone` リポジトリを選択 → **Connect**。
   - リポジトリ直下の `render.yaml` を自動で読み込み、設定が表示されます。
4. 環境変数の入力を求められます（`sync:false` の項目）。**今はLINEの値だけ入れ、空でも進めます：**
   - `REINFOLIB_API_KEY` … まだなら **空のまま**でOK（自動でデモ動作）
   - `LINE_CHANNEL_SECRET` / `LINE_CHANNEL_ACCESS_TOKEN` … LINEチャネルの値（後から設定も可）
   - `DEMO_MODE` … `1`（デモ）のまま
5. **Apply / Create** を押すとビルド＆デプロイ開始。数分で完了します。
6. 発行された URL（例 `https://isoge-clone.onrender.com`）を開く → **Web版が表示**されれば成功🎉
   「サンプル物件で試す」で判定カードが出ます。

> 無料プランはアクセスが無いとスリープします。最初の1回だけ表示に30秒ほどかかることがあります。

---

## ステップ3：LINEとつなぐ

1. [LINE Developers](https://developers.line.biz/) でプロバイダー →
   **Messaging APIチャネル** を作成。
2. 取得した値を **Renderの環境変数** に設定（Render → 該当サービス → **Environment**）：
   - `LINE_CHANNEL_SECRET` ＝ チャネル基本設定の「チャネルシークレット」
   - `LINE_CHANNEL_ACCESS_TOKEN` ＝ Messaging API設定の「チャネルアクセストークン（長期）」
   - 保存すると自動で再デプロイされます。
3. LINE Developersの **Messaging API設定** で：
   - **Webhook URL** ＝ `https://xxxx.onrender.com/callback` を入力 → **Verify（検証）** が成功すること
   - **Webhookの利用** ＝ オン
   - **応答メッセージ** ＝ オフ（自動応答を切る）
4. 同画面のQRから友だち追加 → SUUMOの中古マンションURLを送信 → **判定カードが返信**されれば成功🎉
   （デモモード中はサンプル相場での判定になります）

---

## ステップ4：国交省APIキーが届いたら「実データ」に切り替え

1. Render → サービス → **Environment** で：
   - `REINFOLIB_API_KEY` ＝ 届いたAPIキー
   - `DEMO_MODE` ＝ `0`
2. 保存 → 自動再デプロイ。これ以降は、送られたSUUMO物件の**所在地の実際の取引・成約価格**で判定します。

> `DEMO_MODE` を `0` にしてもキーが未設定なら、安全のため自動でデモ動作に戻ります（エラーで落ちません）。

---

## うまくいかないときは

| 症状 | 対処 |
|------|------|
| Webは出るがLINEが無反応 | Webhook URLの末尾が `/callback` か、Webhook利用=オン、シークレット/トークンが正しいか確認 |
| LINEの検証が失敗 | Renderのデプロイ完了を待つ／URLのスペル確認。Render無料枠のスリープ復帰待ちで数十秒かかることも |
| 「市区町村を特定できません」 | 実データモードでSUUMOの所在地が解析できない場合。デモモードでは発生しません |
| 「取引事例が不足」 | 国交省データが少ない地方エリア等。都市部のURLで再確認 |

---

## 補足：別ホストを使う場合

`Procfile`（`web: gunicorn app:app --bind 0.0.0.0:$PORT`）を同梱しているので、
**Railway / Fly.io / Heroku系** でも同じ要領でデプロイできます。環境変数は同じ3つ＋`DEMO_MODE`を設定してください。
