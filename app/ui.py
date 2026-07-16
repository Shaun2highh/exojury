"""Visual layer: minimal CSS, landing hero, 3D system viewer.

Three.js is vendored in app/assets/three.min.js and inlined into iframes,
so the 3D always works — no CDN, no network dependency.
"""

import json
from functools import lru_cache
from pathlib import Path

ASSETS = Path(__file__).resolve().parent / "assets"

BLUE = "#3987e5"
VIOLET = "#9085e9"
YELLOW = "#c98500"
RED = "#e66767"


@lru_cache(maxsize=1)
def three_js() -> str:
    return (ASSETS / "three.min.js").read_text()


# --------------------------------------------------------------------- CSS
# Minimal design system: one accent, generous space, hairline dividers,
# no boxes unless they group interactive content. CSS starfield (no iframe)
# so the page itself feels alive without clipping or overlap.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] * {
  font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 500px at 12% -10%, rgba(57,135,229,.13), transparent 60%),
    radial-gradient(900px 440px at 90% -6%, rgba(144,133,233,.10), transparent 55%),
    #0a0b0e;
}
[data-testid="stHeader"] { background: rgba(10,11,14,.5); backdrop-filter: blur(8px); }
.block-container { padding-top: 2.2rem; padding-bottom: 4rem; max-width: 1180px; }

/* top navigation */
[data-testid="stTopNav"] { background: transparent; }

/* ---- typography helpers ---- */
.sect { margin: 26px 0 14px 0; }
.eyebrow { font-size: 11px; letter-spacing: .18em; font-weight: 600;
  color: #3987e5; text-transform: uppercase; margin-bottom: 6px; }
.sect-title { font-size: 26px; font-weight: 700; letter-spacing: -.015em;
  color: #fff; line-height: 1.15; }
.sect-sub { color: #8a8f98; font-size: 14.5px; margin-top: 6px; max-width: 760px; }

/* ---- minimal stat row: numbers over hairline, no boxes ---- */
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0; border-top: 1px solid rgba(255,255,255,.08); margin: 10px 0 6px 0; }
.stat { padding: 16px 18px 4px 0; }
.stat + .stat { border-left: 1px solid rgba(255,255,255,.06); padding-left: 18px; }
.stat .v { font-size: 30px; font-weight: 700; color: #fff; letter-spacing: -.02em; }
.stat .l { font-size: 12px; color: #8a8f98; margin-top: 2px; }

/* ---- cards (used sparingly) ---- */
.card { background: rgba(255,255,255,.03); border: 1px solid rgba(255,255,255,.07);
  border-radius: 14px; padding: 18px 20px; height: 100%;
  transition: border-color .2s ease; }
.card:hover { border-color: rgba(57,135,229,.45); }
.card h4 { margin: 0 0 8px 0; font-size: 15.5px; color: #fff; }
.card p { color: #a7acb6; font-size: 13.5px; line-height: 1.55; margin: 0; }
.card .tag { font-size: 11px; font-weight: 700; padding: 2px 10px;
  border-radius: 999px; letter-spacing: .04em; }

/* ---- verdict banner ---- */
.verdict-card { border-radius: 14px; padding: 18px 22px; margin: 4px 0 12px 0;
  border: 1px solid rgba(255,255,255,.09); background: rgba(255,255,255,.03); }
.verdict-card .headline { font-size: 1.45rem; font-weight: 700; }
.verdict-card .sub { color: #a7acb6; font-size: .9rem; margin-top: 4px; }
.chip { display: inline-block; padding: 3px 12px; border-radius: 999px;
  font-size: .76rem; font-weight: 700; margin: 0 8px 6px 0; }

/* ---- key-value grid instead of chip soup ---- */
.kv { display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 1px; background: rgba(255,255,255,.06); border-radius: 12px;
  overflow: hidden; border: 1px solid rgba(255,255,255,.07); margin: 10px 0; }
.kv > div { background: #0e1013; padding: 10px 14px; }
.kv .k { font-size: 11px; color: #8a8f98; letter-spacing: .06em;
  text-transform: uppercase; }
.kv .val { font-size: 14.5px; color: #fff; font-weight: 600; margin-top: 2px; }

.stButton button, .stDownloadButton button, .stLinkButton a {
  border-radius: 10px; border: 1px solid rgba(57,135,229,.35);
  background: rgba(57,135,229,.10); }
.stButton button:hover, .stDownloadButton button:hover, .stLinkButton a:hover {
  border-color: rgba(57,135,229,.8); background: rgba(57,135,229,.18); }

hr { border-color: rgba(255,255,255,.07); }
</style>
"""


def stat_row(stats: list[tuple[str, str]]) -> str:
    return ('<div class="stats">' + "".join(
        f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for v, l in stats) + "</div>")


# -------------------------------------------------------------- 3D scenes

def landing_hero_html() -> str:
    """Full-width 3D hero: slowly rotating planet over a starfield.
    Self-contained (three.js inlined). Text scales with clamp() so nothing
    ever clips or overlaps."""
    return """
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
html,body{margin:0;background:transparent;font-family:'Space Grotesk',sans-serif;overflow:hidden;}
#wrap{position:relative;height:100vh;border-radius:18px;overflow:hidden;
  border:1px solid rgba(255,255,255,.09);background:#0a0b0e;}
#three{position:absolute;inset:0;}
#content{position:absolute;inset:0;z-index:2;display:flex;flex-direction:column;
  justify-content:center;padding:0 min(6%,64px);pointer-events:none;max-width:60%;}
#eyebrow{font-size:clamp(10px,1.2vw,12px);letter-spacing:.2em;color:#3987e5;
  font-weight:600;margin-bottom:10px;}
#title{font-size:clamp(34px,5vw,58px);font-weight:700;letter-spacing:-.025em;
  color:#fff;line-height:1.02;margin:0;
  text-shadow:0 2px 26px rgba(10,11,14,.95),0 0 46px rgba(10,11,14,.8);}
#title span{background:linear-gradient(95deg,#9dc4f4,#b7aefc);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;}
#sub{color:#b6bbc4;font-size:clamp(13px,1.4vw,16px);line-height:1.55;
  margin-top:14px;max-width:480px;
  text-shadow:0 1px 16px rgba(10,11,14,.95),0 0 34px rgba(10,11,14,.85);}
#hint{position:absolute;right:18px;bottom:14px;color:#565b63;font-size:11px;z-index:2;}
</style></head><body>
<div id="wrap"><div id="three"></div>
<div id="content">
  <div id="eyebrow">INDIA HIGH SCHOOL EXOPLANET DATA CHALLENGE</div>
  <h1 id="title">Every candidate world<br>gets a <span>fair trial</span>.</h1>
  <div id="sub">ExoJury reads NASA's Kepler archive the honest way — no answer-key
  columns, calibrated probabilities, a 95% statistical guarantee, and verdicts
  that found real errors in the catalog itself.</div>
</div>
<div id="hint">three.js · drag to rotate</div>
</div>
<script>__THREE__</script>
<script>
const wrap=document.getElementById('wrap'),host=document.getElementById('three');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
function fit(){renderer.setSize(wrap.offsetWidth,wrap.offsetHeight);}
fit();host.appendChild(renderer.domElement);
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(38,wrap.offsetWidth/wrap.offsetHeight,.1,100);
let az=-.55,el=.10;const R=8.2;
function place(){cam.position.set(R*Math.sin(az)*Math.cos(el),R*Math.sin(el),
  R*Math.cos(az)*Math.cos(el));cam.lookAt(2.6,0,0);}
place();
addEventListener('resize',()=>{fit();cam.aspect=wrap.offsetWidth/wrap.offsetHeight;
  cam.updateProjectionMatrix();});

// starfield
const N=1400,pos=new Float32Array(N*3);
for(let i=0;i<N*3;i++)pos[i]=(Math.random()-.5)*90;
const sg=new THREE.BufferGeometry();
sg.setAttribute('position',new THREE.BufferAttribute(pos,3));
const starPts=new THREE.Points(sg,new THREE.PointsMaterial({color:0xaebfd8,size:.07,
  transparent:true,opacity:.85}));
scene.add(starPts);

// planet — gradient-shaded sphere via canvas texture
const tex=document.createElement('canvas');tex.width=512;tex.height=256;
const tc=tex.getContext('2d');
const lg=tc.createLinearGradient(0,0,0,256);
lg.addColorStop(0,'#274d78');lg.addColorStop(.45,'#3987e5');
lg.addColorStop(.75,'#6aa5ec');lg.addColorStop(1,'#274d78');
tc.fillStyle=lg;tc.fillRect(0,0,512,256);
tc.globalAlpha=.16;
for(let i=0;i<38;i++){tc.fillStyle=Math.random()<.5?'#123a63':'#8fc0f2';
  const y=30+Math.random()*200,h=6+Math.random()*22,w=60+Math.random()*220;
  tc.beginPath();tc.ellipse(Math.random()*512,y,w,h,0,0,7);tc.fill();}
const planet=new THREE.Mesh(new THREE.SphereGeometry(2.35,64,64),
  new THREE.MeshStandardMaterial({map:new THREE.CanvasTexture(tex),roughness:.85}));
planet.position.set(2.9,0,0);scene.add(planet);

// atmosphere glow sprite
const gc=document.createElement('canvas');gc.width=gc.height=256;
const g2=gc.getContext('2d');
const gr=g2.createRadialGradient(128,128,80,128,128,128);
gr.addColorStop(0,'rgba(90,160,240,0)');gr.addColorStop(.75,'rgba(90,160,240,.25)');
gr.addColorStop(1,'rgba(90,160,240,0)');
g2.fillStyle=gr;g2.fillRect(0,0,256,256);
const halo=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(gc),
  blending:THREE.AdditiveBlending,transparent:true}));
halo.scale.set(6.4,6.4,1);halo.position.copy(planet.position);scene.add(halo);

// lights: key from the left (like a star off-screen)
const key=new THREE.DirectionalLight(0xfff4e0,2.6);key.position.set(-6,2,4);
scene.add(key);scene.add(new THREE.AmbientLight(0x22344a,1.4));

let drag=false,lx=0,ly=0;
wrap.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;ly=e.clientY;});
addEventListener('pointerup',()=>drag=false);
addEventListener('pointermove',e=>{if(!drag)return;
  az+=(e.clientX-lx)*.006;el=Math.min(.9,Math.max(-.5,el+(e.clientY-ly)*.004));
  lx=e.clientX;ly=e.clientY;place();});

(function tick(t){planet.rotation.y=(t||0)/16000;
  starPts.rotation.y=(t||0)/220000;
  renderer.render(scene,cam);requestAnimationFrame(tick);})();
</script></body></html>""".replace("__THREE__", three_js())


def system_viewer_html(period, prad, srad, steff, teq, depth) -> str:
    """Edge-on system: star + orbiting planet + live light curve.
    Flex column layout — HUD, 3D canvas, light-curve strip — no absolute
    positioning, so nothing can overlap at any width."""
    params = {
        "period": None if period != period else float(period),
        "ror": None if (prad != prad or srad != srad or not srad)
                else max(min(float(prad) / (float(srad) * 109.1), 0.5), 0.008),
        "starColor": _star_color(steff),
        "planetColor": _planet_color(teq),
        "depth": 0.0 if depth != depth else float(depth),
    }
    return """
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600&display=swap');
html,body{margin:0;background:transparent;overflow:hidden;
  font-family:'Space Grotesk',system-ui,sans-serif;}
#wrap{display:flex;flex-direction:column;height:100vh;border-radius:14px;
  overflow:hidden;border:1px solid rgba(255,255,255,.09);background:#0a0b0e;}
#hud{display:flex;justify-content:space-between;align-items:center;
  padding:9px 14px;font-size:11.5px;color:#8a8f98;flex:0 0 auto;}
#hud b{color:#fff;letter-spacing:.06em;}
#three{flex:1 1 auto;min-height:0;position:relative;}
#lc-box{flex:0 0 86px;padding:0 14px 10px 14px;}
#lc-label{font-size:10.5px;color:#8a8f98;margin-bottom:3px;}
#flux{width:100%;height:64px;display:block;border-radius:8px;}
</style>
<script>__THREE__</script>
</head><body>
<div id="wrap">
  <div id="hud"><span><b>SYSTEM VIEW</b> · illustrative geometry, real parameters</span>
  <span>drag to rotate</span></div>
  <div id="three"></div>
  <div id="lc-box"><div id="lc-label">live light curve — watch the transit dip</div>
  <canvas id="flux"></canvas></div>
</div>
<script>
const P = __PARAMS__;
const host=document.getElementById('three');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
function fit(){renderer.setSize(host.offsetWidth,host.offsetHeight);}
host.appendChild(renderer.domElement);fit();
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(42,host.offsetWidth/Math.max(host.offsetHeight,1),.1,100);
let az=0,el=.20;
function place(){cam.position.set(9*Math.sin(az)*Math.cos(el),9*Math.sin(el),
  9*Math.cos(az)*Math.cos(el));cam.lookAt(0,0,0);}
place();
addEventListener('resize',()=>{fit();
  cam.aspect=host.offsetWidth/Math.max(host.offsetHeight,1);cam.updateProjectionMatrix();});

const sg=new THREE.BufferGeometry();
const pos=new Float32Array(900);
for(let i=0;i<900;i++)pos[i]=(Math.random()-.5)*70;
sg.setAttribute('position',new THREE.BufferAttribute(pos,3));
scene.add(new THREE.Points(sg,new THREE.PointsMaterial({color:0x9db4d4,size:.05,
  transparent:true,opacity:.8})));

const starR=1.15;
scene.add(new THREE.Mesh(new THREE.SphereGeometry(starR,48,48),
  new THREE.MeshBasicMaterial({color:P.starColor})));
const gc=document.createElement('canvas');gc.width=gc.height=256;
const g=gc.getContext('2d');
const grd=g.createRadialGradient(128,128,10,128,128,128);
grd.addColorStop(0,P.starColor);grd.addColorStop(.35,P.starColor+'66');
grd.addColorStop(1,'rgba(0,0,0,0)');
g.fillStyle=grd;g.fillRect(0,0,256,256);
const glow=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(gc),
  blending:THREE.AdditiveBlending,transparent:true}));
glow.scale.set(6.2,6.2,1);scene.add(glow);
scene.add(new THREE.PointLight(0xffffff,110,0));
scene.add(new THREE.AmbientLight(0x334455,.6));

const ror=P.ror??0.05;
const planet=new THREE.Mesh(new THREE.SphereGeometry(Math.max(ror*starR*4,0.09),32,32),
  new THREE.MeshStandardMaterial({color:P.planetColor,roughness:.7}));
scene.add(planet);
const orbR=4.2,oPts=[];
for(let i=0;i<=128;i++){const a=i/128*Math.PI*2;
  oPts.push(new THREE.Vector3(orbR*Math.cos(a),0,orbR*Math.sin(a)));}
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(oPts),
  new THREE.LineBasicMaterial({color:0x3a3f4a,transparent:true,opacity:.8})));

let drag=false,lx=0,ly=0;
host.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;ly=e.clientY;});
addEventListener('pointerup',()=>drag=false);
addEventListener('pointermove',e=>{if(!drag)return;
  az+=(e.clientX-lx)*.008;el=Math.min(1.2,Math.max(.05,el+(e.clientY-ly)*.005));
  lx=e.clientX;ly=e.clientY;place();});

const lc=document.getElementById('flux'),lx2=lc.getContext('2d');
function sizeLC(){lc.width=lc.offsetWidth*devicePixelRatio;
  lc.height=lc.offsetHeight*devicePixelRatio;
  lx2.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);}
sizeLC();addEventListener('resize',sizeLC);
const hist=[];
const orbitSec=P.period?Math.min(14,Math.max(4,3+2.2*Math.log10(1+P.period))):7;
const depthFrac=Math.max(P.depth/1e6,0.02);

(function tick(t){
  const a=(t||0)/1000/orbitSec*Math.PI*2;
  planet.position.set(orbR*Math.cos(a),0,orbR*Math.sin(a));
  const inFront=Math.sin(a)>0&&Math.abs(orbR*Math.cos(a))<starR*1.05;
  hist.push(inFront?1-depthFrac:1);
  if(hist.length>320)hist.shift();
  const w=lc.offsetWidth,h=lc.offsetHeight;
  lx2.clearRect(0,0,w,h);
  lx2.fillStyle='rgba(255,255,255,.03)';lx2.fillRect(0,0,w,h);
  lx2.beginPath();lx2.strokeStyle='#3987e5';lx2.lineWidth=1.8;
  hist.forEach((f,i)=>{const x=i/319*w;
    const y=8+(1-((f-(1-depthFrac*1.3))/(depthFrac*1.5)))*(h-16);
    i?lx2.lineTo(x,y):lx2.moveTo(x,y);});
  lx2.stroke();
  renderer.render(scene,cam);
  requestAnimationFrame(tick);
})();
</script></body></html>""".replace("__THREE__", three_js()) \
                          .replace("__PARAMS__", json.dumps(params))


def _star_color(teff) -> str:
    if teff is None or teff != teff:
        return "#ffd9a0"
    if teff < 3900:  return "#ff9d6b"
    if teff < 5300:  return "#ffc46b"
    if teff < 6000:  return "#fff3d6"
    if teff < 7500:  return "#ffffff"
    return "#bcd4ff"


def _planet_color(teq) -> str:
    if teq is None or teq != teq:
        return "#8fa9c9"
    if teq > 1500:  return "#ff6b4a"
    if teq > 700:   return "#d99a5b"
    if teq > 310:   return "#c9b28a"
    if teq > 180:   return "#5b9bd9"
    return "#cfe4f5"
