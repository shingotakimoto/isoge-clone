<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>マンション割安判定サービス ISOGE!（クローン）</title>
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
    <div class="logo">🏢 ISOGE! CLONE</div>
    <h1>マンション割安判定サービス</h1>
    <div class="en">ISOGE!</div>
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

  <footer class="site">© ISOGE! クローン（学習用プロトタイプ）｜データ出典：国土交通省 不動産情報ライブラリ</footer>

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
