"""錄製「系統介紹 + 操作步驟 + 功能說明」示範影片（含中文語音旁白與字幕）。

流程：
1. 以暫存資料庫啟動 API Server（不影響 data/tourism.db），並實際執行 pytest 與 API Client 取得輸出
2. 用 edge-tts 產生每段中文旁白
3. 用 Playwright 操作瀏覽器（投影片 → 終端機 → Swagger UI → ReDoc），以 CDP screencast 擷取畫面
4. 用 ffmpeg 依時間軸合成畫面與旁白，輸出 MP4

額外需求（不在 requirements.txt）：
    pip install playwright edge-tts imageio-ffmpeg
    python -m playwright install chromium    # 或以 --chrome 指定 chrome.exe

用法：
    python scripts/record_demo.py                       # 輸出 video/demo.mp4
    python scripts/record_demo.py --preview             # 只截圖檢查畫面，不合成影片
"""
import argparse
import asyncio
import base64
import glob
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import edge_tts
import imageio_ffmpeg
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.exists():
    PY = Path(sys.executable)
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "zh-TW-HsiaoChenNeural"
API_KEY = "ntub-iot-2026"
REPO_URL = "https://github.com/jerry102039/taiwan-tourism-api"
PALACE = "Attraction_379000000A_000019"  # 國立故宮博物院
TAIPEI101 = "Attraction_379000000A_000217"  # 臺北101
W, H, SCALE = 1440, 810, 4 / 3  # CSS 尺寸 × 縮放 = 1920×1080

# ─────────────────────────────── 旁白 ───────────────────────────────
N = {
    "intro": "大家好，這支影片要介紹「台灣觀光景點 Open Data RESTful API」，內容包含系統介紹、操作步驟與功能說明。",
    "src": "本系統使用交通部觀光署「景點 - 觀光資訊資料庫」的政府開放資料，採用觀光資料標準 V2.1。",
    "scale": "資料涵蓋全台六千兩百多筆景點、二十二個縣市、三百四十八個鄉鎮市區，以及一萬多張景點圖片。",
    "tech": "後端使用 Python 的 FastAPI 框架，搭配 SQLAlchemy 與 SQLite 資料庫，並用 Pydantic 做資料驗證。",
    "arch": "系統啟動時，會自動把原始的 JSON 資料正規化，拆成九張關聯式資料表匯入資料庫。",
    "res": "對外提供八種資源、五十七個 API 操作，包含景點、圖片、類型、縣市、鄉鎮、評論、旅遊行程與統計。",
    "crud": "每個資源都支援完整的 CRUD，也就是查詢、新增、整筆更新、部分更新與刪除。",
    "feat1": "查詢支援關鍵字搜尋、多條件篩選、排序與分頁，還能用經緯度查詢附近的景點。",
    "feat2": "API 遵循 REST 慣例，回傳正確的 HTTP 狀態碼；讀取公開，新增、修改與刪除則需要 API Key。",
    "step1": "接下來示範操作步驟。首先從 GitHub 下載專案，並進入專案資料夾。",
    "step2": "建立 Python 虛擬環境並啟用，再用 pip 安裝需要的套件。",
    "step3": "最後用 uvicorn 啟動伺服器。第一次啟動時，系統會自動把開放資料匯入 SQLite，只要一兩秒。",
    "step4": "伺服器啟動後，用瀏覽器打開 127.0.0.1:8000/docs，就能看到 API 文件。",
    "swagger": "這是 FastAPI 自動產生的 Swagger UI 互動式文件，API 依照資源分組，每個操作都有中文說明。",
    "list1": "先來查詢景點列表。展開 GET attractions，按下 Try it out。",
    "list2": "在關鍵字欄位輸入「老街」，每頁顯示五筆，然後按 Execute 送出。",
    "list3": "伺服器回傳 200，回應包含總筆數、頁碼、總頁數與景點資料，這就是統一的分頁格式。",
    "near1": "接著試試附近景點查詢。輸入台北車站附近的經緯度，搜尋半徑一公里。",
    "near2": "系統用 Haversine 公式計算距離，結果由近到遠排序，並附上每個景點的距離。",
    "detail": "再用景點 ID 查詢單一景點，以國立故宮博物院為例，可以看到地址、營業時間、類型與圖片等完整資料。",
    "auth1": "新增、修改、刪除都需要 API Key。先試著在沒有授權的情況下新增評論，結果回傳 401 錯誤。",
    "auth2": "按右上角的 Authorize 按鈕，輸入 API Key，完成授權。",
    "review": "再送出一次，這次成功新增一則五顆星評論，回傳 201 Created，並在 Location header 附上新資源的網址。",
    "trip1": "接著建立一個旅遊行程，可以在同一個請求裡，一併帶入每天要去的景點。",
    "trip2": "行程建立成功，回應裡包含每一個行程項目，以及對應的景點資訊。",
    "patch": "用 PATCH 只修改行程標題，其他欄位維持不變。",
    "invalid": "如果資料不合法，例如把評分改成六顆星，系統會回傳 422，並清楚說明錯誤原因。",
    "delete": "最後刪除這個行程，成功時回傳 204 No Content，行程項目也會一併刪除。",
    "stats": "統計 API 提供資料總覽，可以看到各資源的數量，包含剛剛新增的評論。",
    "stats2": "也能查詢評價最高的景點，故宮以五顆星排在第一名。",
    "redoc": "另外也提供 ReDoc 格式的文件，方便閱讀完整的 API 規格。",
    "test1": "專案附有自動化測試。執行 pytest，{pytest_n} 個測試案例全部通過。",
    "test2": "也可以用 Python API Client 對執行中的伺服器實際送出 {client_n} 個請求做端對端測試，另外還附有 Postman Collection。",
    "outro": "以上就是台灣觀光景點 Open Data API 的介紹與操作示範。原始碼已經放在 GitHub，歡迎下載使用，謝謝觀看！",
}

# ─────────────────────────────── 畫面覆蓋層（字幕、章節、游標） ───────────────────────────────
OVERLAY_JS = r"""
(() => {
  if (window.__demo) return;
  const css = `
  #dm-cap{position:fixed;left:50%;bottom:26px;transform:translateX(-50%);max-width:84%;z-index:2147483646;
    background:rgba(10,14,22,.82);color:#fff;font:600 23px/1.55 "Microsoft JhengHei","PingFang TC",sans-serif;
    padding:10px 26px;border-radius:12px;text-align:center;letter-spacing:.5px;box-shadow:0 6px 24px rgba(0,0,0,.35);
    transition:opacity .25s}
  #dm-cap:empty{opacity:0}
  #dm-chap{position:fixed;top:12px;right:14px;z-index:2147483646;background:#0f766e;color:#fff;
    font:700 15px "Microsoft JhengHei",sans-serif;padding:6px 14px;border-radius:999px;box-shadow:0 3px 10px rgba(0,0,0,.25)}
  #dm-chap:empty{display:none}
  #dm-cur{position:fixed;left:0;top:0;width:26px;height:26px;z-index:2147483647;pointer-events:none;
    transform:translate(-3px,-2px);filter:drop-shadow(0 2px 3px rgba(0,0,0,.45))}
  .dm-ripple{position:fixed;width:18px;height:18px;margin:-9px 0 0 -9px;border-radius:50%;z-index:2147483646;
    border:3px solid #f59e0b;pointer-events:none;animation:dmr .55s ease-out forwards}
  @keyframes dmr{to{transform:scale(3.2);opacity:0}}
  .dm-hl{outline:4px solid #f59e0b !important;outline-offset:3px;border-radius:6px;transition:outline-color .3s}`;
  const mount = () => {
    if (document.getElementById('dm-cap')) return;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const cap = document.createElement('div'); cap.id = 'dm-cap';
    const chap = document.createElement('div'); chap.id = 'dm-chap';
    const cur = document.createElement('div'); cur.id = 'dm-cur';
    cur.innerHTML = '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M3 2l7.5 19 2.6-7.4L21 11z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    cur.style.left = (window.__dmx || -50) + 'px'; cur.style.top = (window.__dmy || -50) + 'px';
    document.body.append(cap, chap, cur);
  };
  document.addEventListener('mousemove', e => {
    const c = document.getElementById('dm-cur'); if (c) { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }
  }, true);
  document.addEventListener('mousedown', e => {
    const r = document.createElement('div'); r.className = 'dm-ripple';
    r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
    document.body.appendChild(r); setTimeout(() => r.remove(), 600);
  }, true);
  window.__demo = {
    mount,
    cap: t => { mount(); document.getElementById('dm-cap').textContent = t || ''; },
    chap: t => { mount(); document.getElementById('dm-chap').textContent = t || ''; },
    cursor: (x, y) => { mount(); const c = document.getElementById('dm-cur'); c.style.left = x + 'px'; c.style.top = y + 'px'; },
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
})();
"""

# ─────────────────────────────── 投影片 ───────────────────────────────
BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:100%;height:100%;overflow:hidden}
body{font-family:"Microsoft JhengHei","PingFang TC","Segoe UI",sans-serif;color:#e6edf5;
  background:radial-gradient(1200px 700px at 85% -10%,#12506b 0%,transparent 60%),
             radial-gradient(900px 600px at -10% 110%,#3b2a12 0%,transparent 55%),#0b1624}
.wrap{padding:64px 88px 120px;height:100%;display:flex;flex-direction:column}
.eyebrow{color:#5eead4;font-weight:700;letter-spacing:4px;font-size:17px;margin-bottom:12px}
h1{font-size:46px;font-weight:800;letter-spacing:1px}
h2{font-size:38px;font-weight:800;margin-bottom:30px}
.muted{color:#94a3b8}
.r{opacity:0;transform:translateY(18px);transition:opacity .6s ease,transform .6s ease}
.r.on{opacity:1;transform:none}
.card{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:16px;padding:22px 26px}
.chip{display:inline-block;padding:7px 16px;border-radius:999px;background:rgba(94,234,212,.12);color:#99f6e4;
  border:1px solid rgba(94,234,212,.35);font-weight:700;font-size:18px;margin:0 10px 10px 0}
code{font-family:"Cascadia Code",Consolas,monospace}
#dm-cur{display:none!important}
"""

REVEAL_JS = "<script>window.reveal=g=>document.querySelectorAll('.r[data-g=\"'+g+'\"]').forEach(e=>e.classList.add('on'))</script>"


def slide(body: str, extra_css: str = "") -> str:
    return f"<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><title>demo</title><style>{BASE_CSS}{extra_css}</style></head><body>{body}{REVEAL_JS}</body></html>"


SLIDE_TITLE = slide(
    f"""<div class="wrap" style="justify-content:center;padding-bottom:150px">
  <div class="eyebrow r" data-g="1">NTUB IoT APP · OPEN DATA PROJECT</div>
  <h1 class="r" data-g="1" style="font-size:64px;line-height:1.25">台灣觀光景點<br><span style="color:#5eead4">Open Data RESTful API</span></h1>
  <div class="r" data-g="1" style="font-size:28px;margin:26px 0 38px;color:#cbd5e1">系統介紹 ・ 操作步驟 ・ 功能說明</div>
  <div class="r" data-g="1"><span class="chip">Python 3.13</span><span class="chip">FastAPI</span><span class="chip">SQLAlchemy</span><span class="chip">SQLite</span><span class="chip">Swagger / OpenAPI</span></div>
  <div class="r muted" data-g="1" style="margin-top:28px;font-size:19px"><code>{REPO_URL}</code></div>
</div>"""
)

SLIDE_INTRO = slide(
    """<div class="wrap">
  <div class="eyebrow">01 · 系統介紹</div><h2>資料來源與規模</h2>
  <div style="display:grid;grid-template-columns:1.05fr 1fr;gap:34px;flex:1">
    <div class="card r" data-g="1" style="font-size:21px;line-height:1.85">
      <div style="color:#5eead4;font-weight:800;font-size:23px;margin-bottom:8px">交通部觀光署<br>「景點 - 觀光資訊資料庫」</div>
      <div>政府資料開放平臺 #7777</div><div>觀光資料標準 V2.1 ・ 每日更新</div>
      <div class="muted" style="margin-top:8px"><code>data/AttractionList.json</code>（16 MB）</div>
    </div>
    <div class="r" data-g="2" style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
      <div class="card stat"><b>6,226</b><span>景點</span></div><div class="card stat"><b>22</b><span>縣市</span></div>
      <div class="card stat"><b>348</b><span>鄉鎮市區</span></div><div class="card stat"><b>10,725</b><span>景點圖片</span></div>
    </div>
  </div>
  <div class="r" data-g="3" style="margin-top:26px"><span class="chip">FastAPI</span><span class="chip">SQLAlchemy 2</span><span class="chip">SQLite</span><span class="chip">Pydantic 2 資料驗證</span><span class="chip">Uvicorn</span></div>
</div>""",
    ".stat{display:flex;flex-direction:column;justify-content:center}.stat b{font-size:48px;color:#fbbf24;font-weight:800}.stat span{font-size:21px;color:#cbd5e1;margin-top:4px}",
)

SLIDE_ARCH = slide(
    """<div class="wrap">
  <div class="eyebrow">01 · 系統介紹</div><h2>系統架構與資源</h2>
  <div class="flow r" data-g="1">
    <div class="node">AttractionList.json<small>Open Data 原始檔</small></div><i>→</i>
    <div class="node">seed.py 正規化<small>拆成 9 張關聯式資料表</small></div><i>→</i>
    <div class="node">SQLite<small>外鍵 + 串聯刪除</small></div><i>→</i>
    <div class="node hot">FastAPI<small>/api/v1 · 57 個操作</small></div><i>→</i>
    <div class="node">Swagger / Client / Postman</div>
  </div>
  <div class="res r" data-g="2">
    <div class="card"><b>attractions</b>景點</div><div class="card"><b>images</b>景點圖片</div>
    <div class="card"><b>categories</b>景點類型</div><div class="card"><b>cities</b>縣市</div>
    <div class="card"><b>towns</b>鄉鎮市區</div><div class="card"><b>reviews</b>遊客評論</div>
    <div class="card"><b>trips / items</b>旅遊行程</div><div class="card"><b>stats</b>統計（唯讀）</div>
  </div>
  <div class="r" data-g="3" style="margin-top:24px;display:flex;gap:14px;align-items:center;font-size:20px">
    <span class="m g">GET</span><span class="m p">POST</span><span class="m u">PUT</span><span class="m a">PATCH</span><span class="m d">DELETE</span>
    <span class="muted" style="margin-left:8px">每個資源皆支援完整 CRUD</span>
  </div>
</div>""",
    """.flow{display:flex;align-items:stretch;gap:10px;margin-bottom:30px}.flow i{align-self:center;font-style:normal;color:#5eead4;font-size:26px}
.node{flex:1;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:14px;padding:16px 14px;font-weight:800;font-size:19px;text-align:center}
.node small{display:block;font-weight:400;color:#94a3b8;font-size:15px;margin-top:6px}.node.hot{border-color:#5eead4;background:rgba(94,234,212,.12)}
.res{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.res .card{padding:16px 20px;font-size:18px;color:#cbd5e1}
.res b{display:block;color:#fff;font-family:Consolas,monospace;font-size:21px;margin-bottom:4px}
.m{padding:6px 16px;border-radius:8px;font-weight:800;font-family:Consolas,monospace;color:#fff}
.g{background:#2563eb}.p{background:#16a34a}.u{background:#d97706}.a{background:#0d9488}.d{background:#dc2626}""",
)

SLIDE_FEAT = slide(
    """<div class="wrap">
  <div class="eyebrow">01 · 系統介紹</div><h2>功能特色</h2>
  <div class="grid">
    <div class="card r" data-g="1"><b>🔍 強大查詢</b>關鍵字、縣市、類型、免費、標籤等多條件篩選，支援排序與分頁</div>
    <div class="card r" data-g="1"><b>📍 附近景點</b>輸入經緯度與半徑，以 Haversine 公式依距離排序</div>
    <div class="card r" data-g="1"><b>⭐ 加值資源</b>在原始資料之上新增遊客評論與旅遊行程</div>
    <div class="card r" data-g="2"><b>✅ REST 慣例</b>200 / 201 / 204 / 401 / 404 / 409 / 422，Location 與 X-Total-Count header</div>
    <div class="card r" data-g="2"><b>🔒 API Key 保護</b>讀取公開；新增、修改、刪除需在 Header 帶入 API Key</div>
    <div class="card r" data-g="2"><b>🧪 完整測試</b>pytest 自動化測試、Python API Client、Postman Collection</div>
  </div>
</div>""",
    ".grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}.grid .card{font-size:19px;line-height:1.7;color:#cbd5e1;padding:26px}.grid b{display:block;font-size:24px;color:#fff;margin-bottom:10px}",
)

SLIDE_OUTRO = slide(
    f"""<div class="wrap" style="justify-content:center;align-items:center;text-align:center;padding-bottom:150px">
  <div class="eyebrow r" data-g="1">THANK YOU</div>
  <h1 class="r" data-g="1" style="font-size:56px">謝謝觀看</h1>
  <div class="r" data-g="1" style="font-size:24px;margin:22px 0 34px;color:#cbd5e1">台灣觀光景點 Open Data RESTful API</div>
  <div class="card r" data-g="1" style="font-size:22px;line-height:2;text-align:left">
    <div>📦 原始碼　<code style="color:#5eead4">{REPO_URL}</code></div>
    <div>📘 API 文件　<code style="color:#5eead4">http://127.0.0.1:8000/docs</code></div>
    <div>🚀 啟動指令　<code style="color:#5eead4">uvicorn app.main:app --reload</code></div>
  </div>
</div>"""
)

TERMINAL = f"""<!doctype html><html><head><meta charset="utf-8"><title>terminal</title><style>{BASE_CSS}
.win{{position:absolute;left:70px;right:70px;top:48px;bottom:118px;background:#0c0c0c;border-radius:12px;overflow:hidden;
  box-shadow:0 20px 60px rgba(0,0,0,.55);border:1px solid #333;display:flex;flex-direction:column}}
.bar{{height:40px;background:#1f1f1f;display:flex;align-items:center;padding:0 16px;gap:8px;color:#ccc;font-size:15px}}
.bar i{{width:13px;height:13px;border-radius:50%;display:inline-block}}
#t{{flex:1;padding:16px 22px;font:18px/1.55 "Cascadia Code",Consolas,"Microsoft JhengHei",monospace;color:#d4d4d4;overflow:hidden;white-space:pre-wrap;word-break:break-all}}
.ps{{color:#6cb6ff}}.cmd{{color:#fff}}.ok{{color:#3fb950}}.info{{color:#58a6ff}}.dim{{color:#8b949e}}.warn{{color:#d29922}}
.caret{{display:inline-block;width:10px;height:20px;background:#d4d4d4;vertical-align:-3px;animation:b 1s steps(1) infinite}}@keyframes b{{50%{{opacity:0}}}}
</style></head><body><div class="win"><div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i>
<span style="margin-left:10px">Windows PowerShell</span></div><div id="t"></div></div>
<script>
const T=document.getElementById('t');const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const caret=()=>{{T.querySelectorAll('.caret').forEach(c=>c.remove());const c=document.createElement('span');c.className='caret';T.appendChild(c);}};
const scroll=()=>{{T.scrollTop=T.scrollHeight}};
window.prompt_=(cwd)=>{{const s=document.createElement('span');s.className='ps';s.textContent='PS '+cwd+'> ';T.appendChild(s);caret();scroll();}};
window.typeCmd=async(cmd,ms)=>{{const s=document.createElement('span');s.className='cmd';T.insertBefore(s,T.querySelector('.caret'));
  for(const ch of cmd){{s.textContent+=ch;scroll();await sleep(ms||45);}}await sleep(250);T.querySelector('.caret').remove();T.appendChild(document.createTextNode('\\n'));}};
window.out=async(lines,ms)=>{{for(const [cls,txt] of lines){{const s=document.createElement('span');if(cls)s.className=cls;s.textContent=txt+'\\n';T.appendChild(s);scroll();await sleep(ms||40);}}}};
window.clearT=()=>{{T.innerHTML=''}};
</script></body></html>"""


# ─────────────────────────────── 工具函式 ───────────────────────────────
def audio_duration(path: Path) -> float:
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True, errors="ignore").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


async def tts_all(texts: dict[str, str], cache: Path) -> dict[str, tuple[Path, float]]:
    cache.mkdir(parents=True, exist_ok=True)

    async def one(key, text):
        p = cache / f"{key}-{hashlib.md5((VOICE + text).encode()).hexdigest()[:10]}.mp3"
        if not p.exists():
            for attempt in range(4):
                try:
                    await edge_tts.Communicate(text, VOICE, rate="+8%").save(str(p))
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(2)
        return key, (p, audio_duration(p))

    return dict(await asyncio.gather(*(one(k, t) for k, t in texts.items())))


def wait_health(base: str, timeout: float = 60):
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(base + "/health", timeout=2) as r:
                if r.status == 200:
                    return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("API Server 沒有在時間內啟動")


def run_capture(args, **kw) -> str:
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "NO_COLOR": "1"}
    env.update(kw.pop("env", {}))
    r = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, **kw)
    return (r.stdout + r.stderr).replace("\r", "")


def find_chrome(arg: str | None) -> str | None:
    if arg:
        return arg
    hits = sorted(glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright\chromium-*\chrome-win*\chrome.exe")))
    return hits[-1] if hits else None


# ─────────────────────────────── 錄影主程式 ───────────────────────────────
class Recorder:
    def __init__(self, page, work: Path, audio: dict, preview: bool):
        self.page, self.work, self.audio, self.preview = page, work, audio, preview
        self.frames: list[tuple[float, Path]] = []
        self.cues: list[tuple[float, Path]] = []
        self.cap_text = ""
        self.chap_text = ""
        self.mx, self.my = W * 0.6, H * 0.6
        self.cue_end = 0.0
        self.shot_n = 0
        (work / "frames").mkdir(parents=True, exist_ok=True)

    # --- 畫面擷取 ---
    async def start(self):
        self.cdp = await self.page.context.new_cdp_session(self.page)
        self.cdp.on("Page.screencastFrame", lambda p: asyncio.ensure_future(self._frame(p)))
        await self._screencast()

    async def _screencast(self):
        await self.cdp.send(
            "Page.startScreencast",
            {"format": "jpeg", "quality": 92, "maxWidth": int(W * SCALE), "maxHeight": int(H * SCALE), "everyNthFrame": 1},
        )

    async def _frame(self, p):
        t = time.time()
        path = self.work / "frames" / f"{len(self.frames):06d}.jpg"
        path.write_bytes(base64.b64decode(p["data"]))
        self.frames.append((t, path))
        try:
            await self.cdp.send("Page.screencastFrameAck", {"sessionId": p["sessionId"]})
        except Exception:
            pass

    async def stop(self):
        await self.cdp.send("Page.stopScreencast")

    # --- 覆蓋層 ---
    async def _restore(self):
        await self.page.evaluate(OVERLAY_JS)
        await self.page.evaluate(
            "([c,h,x,y])=>{__demo.cap(c);__demo.chap(h);__demo.cursor(x,y);window.__dmx=x;window.__dmy=y}",
            [self.cap_text, self.chap_text, self.mx, self.my],
        )

    async def goto(self, url: str, wait: str = "networkidle"):
        await self.page.goto(url, wait_until=wait)
        await self._restore()

    async def chapter(self, text: str):
        self.chap_text = text
        await self.page.evaluate("t=>__demo.chap(t)", text)

    async def say(self, key: str):
        """開始播放一段旁白（同時顯示字幕），立即返回，讓畫面操作與旁白同步進行。"""
        await self.wait()
        path, dur = self.audio[key]
        self.cap_text = N[key]
        await self.page.evaluate("t=>__demo.cap(t)", N[key])
        now = time.time()
        self.cues.append((now, path))
        self.cue_end = now + dur + 0.45
        if self.preview:
            await self.shot(key)

    async def wait(self, extra: float = 0.0):
        """等待目前這段旁白播完。"""
        left = self.cue_end + extra - time.time()
        if left > 0:
            await asyncio.sleep(left)

    async def shot(self, name: str):
        self.shot_n += 1
        await asyncio.sleep(0.3)
        await self.page.screenshot(path=str(self.work / "preview" / f"{self.shot_n:02d}-{name}.png"))

    # --- 滑鼠與鍵盤 ---
    async def move(self, x: float, y: float, dur: float = 0.42):
        steps = max(8, int(dur * 60))
        sx, sy = self.mx, self.my
        for i in range(1, steps + 1):
            k = i / steps
            k = k * k * (3 - 2 * k)  # smoothstep
            await self.page.mouse.move(sx + (x - sx) * k, sy + (y - sy) * k)
            await asyncio.sleep(dur / steps)
        self.mx, self.my = x, y

    async def scroll_to(self, loc, top: int = 90, dur: float = 0.7):
        await loc.evaluate(
            "(el,top)=>window.scrollTo({top:window.scrollY+el.getBoundingClientRect().top-top,behavior:'smooth'})", top
        )
        await asyncio.sleep(dur)

    async def ensure_visible(self, loc):
        box = await loc.bounding_box()
        if box is None or box["y"] < 60 or box["y"] + box["height"] > H - 120:
            await self.scroll_to(loc, top=int(H * 0.3))

    async def click(self, loc, pause: float = 0.2):
        await loc.wait_for(state="visible")
        await self.ensure_visible(loc)
        box = await loc.bounding_box()
        await self.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        await asyncio.sleep(pause)
        await self.page.mouse.click(self.mx, self.my)
        await asyncio.sleep(0.25)

    async def type_into(self, loc, text: str, delay: int = 110):
        await self.click(loc)
        await loc.fill("")
        await loc.press_sequentially(text, delay=delay)

    async def highlight(self, loc, secs: float = 1.6):
        await loc.evaluate("e=>e.classList.add('dm-hl')")
        await asyncio.sleep(secs)
        await loc.evaluate("e=>e.classList.remove('dm-hl')")


# ─────────────────────────────── Swagger UI 操作 ───────────────────────────────
class Swagger:
    def __init__(self, rec: Recorder):
        self.rec, self.page = rec, rec.page

    def op(self, method: str, path: str):
        return self.page.locator(f'.opblock.opblock-{method}:has(.opblock-summary-path[data-path="{path}"])').first

    async def open(self, method: str, path: str):
        op = self.op(method, path)
        await self.rec.scroll_to(op, top=70)
        await self.rec.click(op.locator(".opblock-summary-path"))
        await op.locator(".opblock-body").wait_for()
        await asyncio.sleep(0.4)
        return op

    async def close(self, op):
        await self.rec.scroll_to(op, top=70, dur=0.5)
        await op.locator(".opblock-summary-path").click()
        await asyncio.sleep(0.3)

    async def try_it(self, op):
        await self.rec.click(op.locator("button.try-out__btn"))
        await asyncio.sleep(0.3)

    def param(self, op, name: str):
        return op.locator(f'tr[data-param-name="{name}"] input').first

    async def body(self, op, obj):
        ta = op.locator("textarea.body-param__text")
        await self.rec.ensure_visible(ta)
        await self.rec.click(ta)
        await ta.fill(json.dumps(obj, ensure_ascii=False, indent=2))
        await asyncio.sleep(0.5)

    async def execute(self, op, show_top: int = 80):
        await self.rec.click(op.locator("button.execute"))
        resp = op.locator(".live-responses-table")
        await resp.wait_for()
        await asyncio.sleep(0.5)
        await self.rec.scroll_to(resp, top=show_top)
        status = op.locator(".live-responses-table .response-col_status").first
        await self.rec.highlight(status, 1.0)
        if self.rec.preview:
            await self.rec.shot("exec")
        return resp

    async def response_json(self, op):
        txt = await op.locator(".live-responses-table .response-col_description pre").first.inner_text()
        try:
            return json.loads(txt)
        except ValueError:
            return None

    async def scroll_response_to(self, op, text: str):
        """把回應內容捲動到指定文字所在的位置。"""
        pre = op.locator(".live-responses-table .response-col_description pre").first
        await pre.evaluate(
            """(pre, text) => {
              const w = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
              let n;
              while ((n = w.nextNode())) {
                const i = n.textContent.indexOf(text);
                if (i >= 0) {
                  const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + text.length);
                  const top = r.getBoundingClientRect().top - pre.getBoundingClientRect().top + pre.scrollTop - 60;
                  pre.scrollTo({top, behavior: 'smooth'}); return;
                }
              }
            }""",
            text,
        )
        await asyncio.sleep(1.0)

    async def scroll_response(self, op, px: int = 260, times: int = 2):
        pre = op.locator(".live-responses-table .response-col_description pre").first
        for _ in range(times):
            await pre.evaluate("(e,px)=>e.scrollBy({top:px,behavior:'smooth'})", px)
            await asyncio.sleep(0.9)


# ─────────────────────────────── 劇本 ───────────────────────────────
async def scenario(rec: Recorder, base: str, logs: dict):
    page = rec.page
    sw = Swagger(rec)

    async def show_slide(name):
        await rec.goto(f"{base}/__demo/{name}", wait="load")

    # ── 開場 ──
    await show_slide("title")
    await asyncio.sleep(0.6)
    await page.evaluate("reveal(1)")
    await asyncio.sleep(1.0)
    await rec.say("intro")
    await rec.wait(0.4)

    # ── 01 系統介紹 ──
    await show_slide("intro")
    await rec.chapter("① 系統介紹")
    await asyncio.sleep(0.4)
    await page.evaluate("reveal(1)")
    await rec.say("src")
    await rec.wait()
    await page.evaluate("reveal(2)")
    await rec.say("scale")
    await rec.wait()
    await page.evaluate("reveal(3)")
    await rec.say("tech")

    await rec.wait()
    await show_slide("arch")
    await page.evaluate("reveal(1)")
    await rec.say("arch")
    await rec.wait()
    await page.evaluate("reveal(2)")
    await rec.say("res")
    await rec.wait()
    await page.evaluate("reveal(3)")
    await rec.say("crud")

    await rec.wait()
    await show_slide("feat")
    await page.evaluate("reveal(1)")
    await rec.say("feat1")
    await rec.wait()
    await page.evaluate("reveal(2)")
    await rec.say("feat2")

    # ── 02 操作步驟 ──
    await rec.wait()
    await show_slide("terminal")
    await rec.chapter("② 操作步驟")
    cwd0 = r"C:\Users\demo"
    cwd1 = DEMO_CWD
    await page.evaluate("c=>prompt_(c)", cwd0)
    await rec.say("step1")
    await page.evaluate("c=>typeCmd(c,40)", f"git clone {REPO_URL}.git")
    await page.evaluate(
        "l=>out(l,120)",
        [["", "Cloning into 'taiwan-tourism-api'..."], ["", "Receiving objects: 100% (51/51), 3.47 MiB | 8.20 MiB/s, done."]],
    )
    await page.evaluate("c=>prompt_(c)", cwd0)
    await page.evaluate("c=>typeCmd(c,45)", "cd taiwan-tourism-api")
    await page.evaluate("c=>prompt_(c)", cwd1)
    await rec.say("step2")
    await page.evaluate("c=>typeCmd(c,45)", "python -m venv .venv")
    await page.evaluate("c=>prompt_(c)", cwd1)
    await page.evaluate("c=>typeCmd(c,45)", r".venv\Scripts\activate")
    await page.evaluate("c=>prompt_(c)", "(.venv) " + cwd1)
    await page.evaluate("c=>typeCmd(c,45)", "pip install -r requirements.txt")
    await page.evaluate("l=>out(l,160)", logs["pip"])
    await page.evaluate("c=>prompt_(c)", "(.venv) " + cwd1)
    await rec.say("step3")
    await page.evaluate("c=>typeCmd(c,45)", "uvicorn app.main:app --reload")
    await page.evaluate("l=>out(l,260)", logs["server"])
    if rec.preview:
        await rec.shot("server-out")
    await rec.say("step4")
    await rec.wait(0.2)

    # ── 03 功能示範（Swagger UI） ──
    await rec.goto(f"{base}/docs")
    await page.locator(".opblock").first.wait_for()
    await rec.chapter("③ 功能示範 · Swagger UI")
    await rec.say("swagger")
    await rec.move(W * 0.5, H * 0.45)
    for _ in range(4):
        await page.evaluate("window.scrollBy({top:520,behavior:'smooth'})")
        await asyncio.sleep(1.1)
    await rec.wait()
    await page.evaluate("window.scrollTo({top:0,behavior:'smooth'})")
    await asyncio.sleep(0.9)

    # 查詢景點列表
    await rec.say("list1")
    op = await sw.open("get", "/api/v1/attractions")
    await sw.try_it(op)
    await rec.say("list2")
    await rec.type_into(sw.param(op, "q"), "老街", delay=260)
    await rec.type_into(sw.param(op, "page_size"), "5", delay=150)
    await sw.execute(op)
    await rec.say("list3")
    await sw.scroll_response(op, 240, 3)
    await rec.wait()
    await sw.close(op)

    # 附近景點
    await rec.say("near1")
    op = await sw.open("get", "/api/v1/attractions/nearby")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "lat"), "25.0478", delay=90)
    await rec.type_into(sw.param(op, "lon"), "121.5170", delay=90)
    await rec.type_into(sw.param(op, "radius_km"), "1", delay=150)
    await rec.type_into(sw.param(op, "limit"), "5", delay=150)
    await rec.wait()
    await sw.execute(op)
    await rec.say("near2")
    await sw.scroll_response_to(op, '"distance_km"')
    await rec.highlight(op.locator(".live-responses-table .response-col_description pre").first, 1.2)
    if rec.preview:
        await rec.shot("distance")
    await rec.wait()
    await sw.close(op)

    # 單一景點
    await rec.say("detail")
    op = await sw.open("get", "/api/v1/attractions/{attraction_id}")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "attraction_id"), PALACE, delay=35)
    await sw.execute(op)
    await sw.scroll_response(op, 260, 3)
    await rec.wait()
    await sw.close(op)

    # 未授權 → 401
    await rec.chapter("③ 功能示範 · 新增 / 修改 / 刪除")
    await rec.say("auth1")
    op = await sw.open("post", "/api/v1/attractions/{attraction_id}/reviews")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "attraction_id"), PALACE, delay=25)
    review = {
        "author": "小明",
        "rating": 5,
        "title": "館藏精彩",
        "content": "翠玉白菜與肉形石都很值得一看，建議預留半天。",
        "visit_date": "2026-09-20",
    }
    await sw.body(op, review)
    await sw.execute(op)
    await rec.wait()

    # Authorize
    await rec.say("auth2")
    await page.evaluate("window.scrollTo({top:0,behavior:'smooth'})")
    await asyncio.sleep(0.9)
    await rec.click(page.locator(".auth-wrapper button.authorize"))
    modal = page.locator(".modal-ux")
    await modal.wait_for()
    await rec.type_into(modal.locator("input").first, API_KEY, delay=90)
    await rec.click(modal.locator(".auth-btn-wrapper button.authorize"))
    await asyncio.sleep(0.6)
    await rec.click(modal.locator("button.btn-done, button.close-modal").first)
    await rec.wait()

    # 再送一次 → 201
    await rec.say("review")
    await rec.scroll_to(op.locator("button.execute"), top=int(H * 0.45))
    await sw.execute(op)
    created = await sw.response_json(op) or {}
    review_id = created.get("id", 1)
    loc_header = op.locator(".live-responses-table .response-col_description pre").nth(1)
    if await loc_header.count():
        await rec.ensure_visible(loc_header)
        await rec.highlight(loc_header, 1.6)
    await rec.wait()
    await sw.close(op)

    # 建立行程
    await rec.say("trip1")
    op = await sw.open("post", "/api/v1/trips")
    await sw.try_it(op)
    trip = {
        "title": "台北文化一日遊",
        "description": "故宮看國寶，晚上登 101 看夜景",
        "owner": "小明",
        "start_date": "2026-10-10",
        "end_date": "2026-10-10",
        "items": [
            {"attraction_id": PALACE, "day": 1, "sequence": 1, "note": "上午參觀故宮"},
            {"attraction_id": TAIPEI101, "day": 1, "sequence": 2, "note": "傍晚上觀景台"},
        ],
    }
    await sw.body(op, trip)
    await rec.wait()
    await sw.execute(op)
    trip_out = await sw.response_json(op) or {}
    trip_id = trip_out.get("id", 1)
    await rec.say("trip2")
    await sw.scroll_response(op, 260, 3)
    await rec.wait()
    await sw.close(op)

    # PATCH 行程
    await rec.say("patch")
    op = await sw.open("patch", "/api/v1/trips/{trip_id}")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "trip_id"), str(trip_id), delay=120)
    await sw.body(op, {"title": "台北文化一日遊（含夜景）"})
    await sw.execute(op)
    await rec.wait()
    await sw.close(op)

    # 422 驗證錯誤
    await rec.say("invalid")
    op = await sw.open("patch", "/api/v1/reviews/{review_id}")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "review_id"), str(review_id), delay=120)
    await sw.body(op, {"rating": 6})
    await sw.execute(op)
    await rec.wait()
    await sw.close(op)

    # DELETE → 204
    await rec.say("delete")
    op = await sw.open("delete", "/api/v1/trips/{trip_id}")
    await sw.try_it(op)
    await rec.type_into(sw.param(op, "trip_id"), str(trip_id), delay=120)
    await sw.execute(op)
    await rec.wait()
    await sw.close(op)

    # 統計
    await rec.chapter("③ 功能示範 · 統計與文件")
    await rec.say("stats")
    op = await sw.open("get", "/api/v1/stats/overview")
    await sw.try_it(op)
    await sw.execute(op)
    await asyncio.sleep(0.8)
    await rec.wait()
    await sw.close(op)
    await rec.say("stats2")
    op = await sw.open("get", "/api/v1/stats/top-rated")
    await sw.try_it(op)
    await sw.execute(op)
    await rec.wait(0.3)

    # ReDoc
    await rec.goto(f"{base}/redoc")
    await page.locator("h1").first.wait_for()
    await rec.say("redoc")
    await rec.move(W * 0.62, H * 0.5)
    await page.mouse.wheel(0, 600)
    await asyncio.sleep(1.2)
    nearby_label = page.locator("label", has_text="查詢附近景點").first
    if not await nearby_label.is_visible():
        await rec.click(page.locator("label", has_text="Attractions 景點").first)
        await asyncio.sleep(0.6)
    await rec.click(nearby_label)
    await asyncio.sleep(1.5)
    if rec.preview:
        await rec.shot("redoc-op")
    await rec.wait()

    # ── 04 測試 ──
    await show_slide("terminal")
    await rec.chapter("④ 自動化測試")
    await page.evaluate("c=>prompt_(c)", "(.venv) " + cwd1)
    await rec.say("test1")
    await page.evaluate("c=>typeCmd(c,45)", "pytest -v")
    await page.evaluate("l=>out(l,55)", logs["pytest"])
    if rec.preview:
        await rec.shot("pytest-out")
    await rec.wait(0.6)
    await page.evaluate("clearT()")
    await page.evaluate("c=>prompt_(c)", "(.venv) " + cwd1)
    await rec.say("test2")
    await page.evaluate("c=>typeCmd(c,40)", "python client/api_client.py")
    await page.evaluate("l=>out(l,35)", logs["client"])
    if rec.preview:
        await rec.shot("client-out")
    await rec.wait(0.6)

    # ── 結語 ──
    await show_slide("outro")
    await rec.chapter("")
    await page.evaluate("reveal(1)")
    await rec.say("outro")
    await rec.wait(1.5)


# ─────────────────────────────── 前置：伺服器、輸出擷取 ───────────────────────────────
DEMO_CWD = r"C:\Users\demo\taiwan-tourism-api"


def color_lines(text: str, rules) -> list[list[str]]:
    # 隱藏本機路徑，影片中統一顯示示範路徑
    for local in {str(ROOT), ROOT.as_posix()}:
        text = text.replace(local, DEMO_CWD)
    out = []
    for line in text.splitlines():
        cls = ""
        for pat, c in rules:
            if re.search(pat, line):
                cls = c
                break
        out.append([cls, line])
    return out


def prepare(work: Path, port: int):
    base = f"http://127.0.0.1:{port}"
    for old in work.glob("demo*.db"):
        try:
            old.unlink()
        except OSError:
            pass
    db = work / f"demo-{int(time.time())}-0.db"
    log = open(work / "server.log", "w", encoding="utf-8")
    env = {**os.environ, "DB_FILE": str(db), "API_KEY": API_KEY, "PYTHONIOENCODING": "utf-8"}
    server = subprocess.Popen(
        [str(PY), "-m", "uvicorn", "app.main:app", "--port", str(port)], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
    )
    wait_health(base)
    time.sleep(0.5)
    server_lines = [l for l in (work / "server.log").read_text(encoding="utf-8").splitlines() if "GET /health" not in l]

    print("執行 pytest …")
    pytest_out = run_capture([str(PY), "-m", "pytest", "-v", "-p", "no:cacheprovider", "--color=no"])
    pytest_n = len(re.findall(r" PASSED", pytest_out))
    m = re.search(r"=+ (\d+) passed", pytest_out)
    if m:
        pytest_n = int(m.group(1))
    print("執行 API Client …")
    client_out = run_capture([str(PY), "client/api_client.py", "--base-url", base])
    client_n = len(re.findall(r"PASS", client_out))
    # API Client 會新增並刪除資料；錄影前重建資料庫，保持示範資料乾淨
    server.terminate()
    server.wait()
    env["DB_FILE"] = str(work / f"demo-{int(time.time())}.db")
    log = open(work / "server2.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [str(PY), "-m", "uvicorn", "app.main:app", "--port", str(port)], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT
    )
    wait_health(base)

    pkgs = [l.split("==")[0].split("[")[0] for l in (ROOT / "requirements.txt").read_text().split() if l.strip()]
    logs = {
        "pip": [["dim", "Collecting " + p + " ..."] for p in pkgs[:4]]
        + [["dim", "..."], ["ok", "Successfully installed " + " ".join(pkgs) + " ..."]],
        "server": color_lines("\n".join(server_lines), [(r"imported", "ok"), (r"INFO", "info")]),
        "pytest": color_lines(
            "\n".join(pytest_out.strip().splitlines()[-32:]), [(r"PASSED|passed", "ok"), (r"FAILED|ERROR", "warn")]
        ),
        "client": color_lines("\n".join(client_out.strip().splitlines()[-30:]), [(r"PASS", "ok"), (r"FAIL", "warn")]),
    }
    print(f"pytest：{pytest_n} passed；API Client：{client_n} PASS")
    return server, base, logs, pytest_n, client_n


def build_video(rec: Recorder, work: Path, out: Path):
    frames = rec.frames
    t0 = frames[0][0]
    lst = work / "frames.txt"
    with open(lst, "w", encoding="utf-8") as f:
        for i, (t, p) in enumerate(frames):
            dur = (frames[i + 1][0] - t) if i + 1 < len(frames) else 1.0
            f.write(f"file '{p.as_posix()}'\nduration {max(dur, 0.001):.4f}\n")
        f.write(f"file '{frames[-1][1].as_posix()}'\n")

    args = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(lst)]
    filters = []
    for i, (t, p) in enumerate(rec.cues):
        args += ["-i", str(p)]
        ms = max(0, int((t - t0) * 1000))
        filters.append(f"[{i + 1}:a]adelay={ms}|{ms},aresample=48000[a{i}]")
    mix = "".join(f"[a{i}]" for i in range(len(rec.cues)))
    filters.append(f"{mix}amix=inputs={len(rec.cues)}:normalize=0:dropout_transition=0[aout]")
    total = frames[-1][0] - t0 + 1.0
    args += [
        "-filter_complex", ";".join(filters),
        "-map", "0:v", "-map", "[aout]",
        "-vf", "fps=30,scale=1920:1080:flags=lanczos:out_range=tv,format=yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-color_range", "tv",
        "-c:a", "aac", "-b:a", "160k",
        "-t", f"{total:.2f}", "-movflags", "+faststart", str(out),
    ]  # fmt: skip
    subprocess.run(args, check=True, capture_output=True)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "video" / "demo.mp4")
    ap.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()) / "tourism-demo")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--chrome", help="chrome.exe 路徑（預設使用 Playwright 已安裝的 Chromium）")
    ap.add_argument("--preview", action="store_true", help="只截圖檢查每段畫面")
    a = ap.parse_args()

    work = a.work
    shutil.rmtree(work / "frames", ignore_errors=True)
    shutil.rmtree(work / "preview", ignore_errors=True)
    (work / "preview").mkdir(parents=True, exist_ok=True)

    server, base, logs, pytest_n, client_n = prepare(work, a.port)
    N["test1"] = N["test1"].format(pytest_n=pytest_n)
    N["test2"] = N["test2"].format(client_n=client_n)
    try:
        print("產生語音旁白 …")
        audio = await tts_all(N, work / "tts")
        print(f"旁白總長 {sum(d for _, d in audio.values()):.1f} 秒")

        slides = {"title": SLIDE_TITLE, "intro": SLIDE_INTRO, "arch": SLIDE_ARCH, "feat": SLIDE_FEAT, "outro": SLIDE_OUTRO, "terminal": TERMINAL}
        async with async_playwright() as p:
            browser = await p.chromium.launch(executable_path=find_chrome(a.chrome))
            ctx = await browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=SCALE, locale="zh-TW")
            await ctx.add_init_script(OVERLAY_JS)
            await ctx.route(
                re.compile(r".*/__demo/.*"),
                lambda route: route.fulfill(content_type="text/html; charset=utf-8", body=slides[route.request.url.rsplit("/", 1)[-1]]),
            )
            page = await ctx.new_page()
            await page.goto(f"{base}/__demo/title", wait_until="load")
            rec = Recorder(page, work, audio, a.preview)
            await rec.start()
            await asyncio.sleep(0.5)
            try:
                await scenario(rec, base, logs)
            finally:
                await rec.stop()
                await asyncio.sleep(0.3)
                await browser.close()
    finally:
        server.terminate()

    if a.preview:
        print(f"預覽截圖：{work / 'preview'}")
        return
    print(f"擷取 {len(rec.frames)} 張畫面，合成影片 …")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    build_video(rec, work, a.out)
    print(f"完成：{a.out}（{a.out.stat().st_size / 1e6:.1f} MB）")


if __name__ == "__main__":
    asyncio.run(main())
