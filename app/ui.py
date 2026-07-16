"""Visual layer for the ExoJury dashboard: CSS, animated hero, 3D viewer."""

import json

BLUE = "#3987e5"
VIOLET = "#9085e9"
YELLOW = "#c98500"
RED = "#e66767"
INK2 = "#c3c2b7"
MUTED = "#898781"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [data-testid="stAppViewContainer"] * {
  font-family: 'Space Grotesk', system-ui, -apple-system, sans-serif;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 520px at 15% -8%, rgba(57,135,229,.17), transparent 60%),
    radial-gradient(900px 460px at 88% -4%, rgba(144,133,233,.13), transparent 55%),
    radial-gradient(700px 700px at 50% 115%, rgba(57,135,229,.07), transparent 60%),
    #0b0c10;
}
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.1rem; max-width: 1280px; }

/* ---- tabs as pills ---- */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 6px; background: rgba(255,255,255,.035); padding: 6px;
  border-radius: 14px; border: 1px solid rgba(255,255,255,.08); }
[data-testid="stTabs"] button {
  border-radius: 10px !important; padding: 6px 16px; }
[data-testid="stTabs"] button[aria-selected="true"] {
  background: linear-gradient(135deg, rgba(57,135,229,.28), rgba(144,133,233,.22));
  border: 1px solid rgba(57,135,229,.35); }
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-border"] { display: none; }

/* ---- glass cards ---- */
.kpi-row { display:flex; gap:12px; flex-wrap:wrap; margin: 2px 0 10px 0; }
.kpi { flex:1 1 190px; background: rgba(255,255,255,.045);
  backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px);
  border:1px solid rgba(255,255,255,.10); border-radius:16px;
  padding:15px 18px; transition: transform .22s ease, box-shadow .22s ease,
  border-color .22s ease; }
.kpi:hover { transform: translateY(-4px);
  box-shadow: 0 14px 34px rgba(57,135,229,.16); border-color: rgba(57,135,229,.4); }
.kpi .v { font-size:1.7rem; font-weight:700;
  background: linear-gradient(100deg, #fff 30%, #9dc4f4);
  -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent; }
.kpi .l { color:#898781; font-size:.8rem; margin-top:2px; }

.verdict-card { border-radius:16px; padding:18px 22px; margin:6px 0 14px 0;
  border:1px solid rgba(255,255,255,.12); background: rgba(255,255,255,.045);
  backdrop-filter: blur(14px); }
.verdict-card .headline { font-size:1.5rem; font-weight:700; }
.verdict-card .sub { color:#c3c2b7; font-size:.93rem; margin-top:4px; }
.chip { display:inline-block; padding:3px 12px; border-radius:999px;
  font-size:.78rem; font-weight:700; margin:0 8px 6px 0; }
.info-chips { display:flex; flex-wrap:wrap; gap:8px; margin: 4px 0 10px 0; }
.ichip { background: rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.10);
  border-radius:10px; padding:7px 12px; font-size:.82rem; color:#c3c2b7;
  transition: border-color .2s; }
.ichip b { color:#fff; }
.ichip:hover { border-color: rgba(57,135,229,.45); }

.story { background: rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.10);
  backdrop-filter: blur(14px); border-radius:14px; padding:16px 18px; height:100%;
  transition: transform .22s ease, box-shadow .22s ease; }
.story:hover { transform: translateY(-3px); box-shadow: 0 12px 30px rgba(0,0,0,.35); }
.story h4 { margin:0 0 6px 0; font-size:1.0rem; }
.story p { color:#c3c2b7; font-size:.86rem; margin:4px 0; }
.story .tag { font-size:.73rem; font-weight:700; padding:2px 10px; border-radius:999px; }

.stButton button, .stDownloadButton button {
  border-radius: 10px; border: 1px solid rgba(57,135,229,.4);
  background: linear-gradient(135deg, rgba(57,135,229,.22), rgba(144,133,233,.16));
  transition: box-shadow .2s; }
.stButton button:hover, .stDownloadButton button:hover {
  box-shadow: 0 6px 22px rgba(57,135,229,.3); }
h2, h3 { letter-spacing: -.01em; }
</style>
"""


def hero_html(kpis: list[tuple[str, str]]) -> str:
    """Animated starfield hero with gradient title and KPI chips."""
    chips = "".join(
        f'<div class="hk"><div class="v">{v}</div><div class="l">{l}</div></div>'
        for v, l in kpis)
    return """
<!DOCTYPE html><html><head><style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');
html,body{margin:0;background:transparent;font-family:'Space Grotesk',sans-serif;overflow:hidden;}
#wrap{position:relative;height:300px;border-radius:20px;overflow:hidden;
  border:1px solid rgba(255,255,255,.10);
  background:radial-gradient(900px 340px at 20% 0%, rgba(57,135,229,.25), transparent 60%),
             radial-gradient(700px 300px at 85% 15%, rgba(144,133,233,.20), transparent 55%),
             #0b0c10;}
canvas{position:absolute;inset:0;}
#content{position:relative;z-index:2;padding:38px 44px;}
#title{font-size:44px;font-weight:700;letter-spacing:-.02em;margin:0;
  background:linear-gradient(95deg,#ffffff 20%,#9dc4f4 55%,#b7aefc 80%);
  background-size:200% 100%;-webkit-background-clip:text;background-clip:text;
  -webkit-text-fill-color:transparent;animation:shine 7s linear infinite;}
@keyframes shine{0%{background-position:0% 0}100%{background-position:200% 0}}
#sub{color:#c3c2b7;font-size:15.5px;margin:8px 0 20px 0;max-width:820px;}
#chips{display:flex;gap:12px;flex-wrap:wrap;}
.hk{background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.12);
  backdrop-filter:blur(10px);border-radius:13px;padding:10px 16px;min-width:130px;}
.hk .v{font-size:21px;font-weight:700;color:#fff;}
.hk .l{font-size:11px;color:#898781;margin-top:2px;}
</style></head><body>
<div id="wrap"><canvas id="stars"></canvas>
<div id="content">
  <h1 id="title">ExoJury</h1>
  <div id="sub">Every Kepler candidate gets a fair trial &mdash; a calibrated
  verdict, a 95% statistical guarantee, and a written opinion.
  Leakage-audited &middot; physics only &middot; built on NASA's KOI archive.</div>
  <div id="chips">""" + chips + """</div>
</div></div>
<script>
const cv=document.getElementById('stars'),cx=cv.getContext('2d');
let W,H,stars=[];
function size(){W=cv.width=cv.offsetWidth;H=cv.height=cv.offsetHeight;
  stars=Array.from({length:130},()=>({x:Math.random()*W,y:Math.random()*H,
  r:Math.random()*1.4+.3,p:Math.random()*Math.PI*2,s:.4+Math.random()*1.2}));}
size();window.addEventListener('resize',size);
function tick(t){cx.clearRect(0,0,W,H);
  for(const st of stars){const a=.25+.55*Math.abs(Math.sin(t/1400*st.s+st.p));
    cx.globalAlpha=a;cx.fillStyle=st.r>1.1?'#9dc4f4':'#ffffff';
    cx.beginPath();cx.arc(st.x,st.y,st.r,0,7);cx.fill();
    st.x+=st.s*.06; if(st.x>W+2)st.x=-2;}
  cx.globalAlpha=1;requestAnimationFrame(tick);}
requestAnimationFrame(tick);
</script></body></html>"""


def star_color(teff) -> str:
    if teff is None or teff != teff:
        return "#ffd9a0"
    if teff < 3900:  return "#ff9d6b"
    if teff < 5300:  return "#ffc46b"
    if teff < 6000:  return "#fff3d6"
    if teff < 7500:  return "#ffffff"
    return "#bcd4ff"


def planet_color(teq) -> str:
    if teq is None or teq != teq:
        return "#8fa9c9"
    if teq > 1500:  return "#ff6b4a"
    if teq > 700:   return "#d99a5b"
    if teq > 310:   return "#c9b28a"
    if teq > 180:   return "#5b9bd9"
    return "#cfe4f5"


def system_viewer_html(period, prad, srad, steff, teq, depth, name) -> str:
    """Three.js edge-on system: star + orbiting planet + live light curve.

    Purely illustrative — geometry is scaled for visibility, but orbital
    speed, relative planet size, star colour and transit depth all derive
    from the object's fitted parameters.
    """
    params = {
        "period": None if period != period else float(period),
        "ror": None if (prad != prad or srad != srad or not srad)
                else max(min(float(prad) / (float(srad) * 109.1), 0.5), 0.008),
        "starColor": star_color(steff),
        "planetColor": planet_color(teq),
        "depth": 0.0 if depth != depth else float(depth),
        "name": str(name),
    }
    return """
<!DOCTYPE html><html><head><style>
html,body{margin:0;background:transparent;overflow:hidden;
  font-family:'Space Grotesk',system-ui,sans-serif;}
#wrap{position:relative;height:395px;border-radius:16px;overflow:hidden;
  border:1px solid rgba(255,255,255,.10);background:#0b0c10;}
#hud{position:absolute;top:10px;left:14px;z-index:3;color:#c3c2b7;font-size:12px;}
#hud b{color:#fff;font-size:13px;}
#flux{position:absolute;bottom:8px;left:14px;right:14px;z-index:3;height:74px;
  width:calc(100% - 28px);}
#fluxlabel{position:absolute;bottom:86px;left:16px;color:#898781;font-size:10.5px;z-index:3;}
#drag{position:absolute;top:10px;right:14px;color:#565550;font-size:10.5px;z-index:3;}
</style>
<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
</head><body>
<div id="wrap">
  <div id="hud"><b>SYSTEM VIEW</b> · illustrative geometry, real parameters</div>
  <div id="drag">drag to orbit the camera</div>
  <div id="fluxlabel">live light curve — watch the transit dip</div>
  <canvas id="flux" class="lc"></canvas>
</div>
<script>
const P = """ + json.dumps(params) + """;
const wrap=document.getElementById('wrap');
const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(wrap.offsetWidth,wrap.offsetHeight);
renderer.domElement.style.position='absolute';renderer.domElement.style.inset=0;
wrap.insertBefore(renderer.domElement,document.getElementById('flux'));
const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(42,wrap.offsetWidth/wrap.offsetHeight,.1,100);
let az=0.0, el=0.22;
function placeCam(){cam.position.set(9*Math.sin(az)*Math.cos(el),9*Math.sin(el),
  9*Math.cos(az)*Math.cos(el));cam.lookAt(0,0,0);}
placeCam();

// background stars
const sg=new THREE.BufferGeometry();
const pos=new Float32Array(900);
for(let i=0;i<900;i++)pos[i]=(Math.random()-.5)*70;
sg.setAttribute('position',new THREE.BufferAttribute(pos,3));
scene.add(new THREE.Points(sg,new THREE.PointsMaterial({color:0x9db4d4,size:.05,transparent:true,opacity:.8})));

// star with glow sprite
const starR=1.15;
const star=new THREE.Mesh(new THREE.SphereGeometry(starR,48,48),
  new THREE.MeshBasicMaterial({color:P.starColor}));
scene.add(star);
const glowCv=document.createElement('canvas');glowCv.width=glowCv.height=256;
const g=glowCv.getContext('2d');
const grd=g.createRadialGradient(128,128,10,128,128,128);
grd.addColorStop(0,P.starColor);grd.addColorStop(.35,P.starColor+'66');
grd.addColorStop(1,'rgba(0,0,0,0)');
g.fillStyle=grd;g.fillRect(0,0,256,256);
const glow=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(glowCv),
  blending:THREE.AdditiveBlending,transparent:true}));
glow.scale.set(6.5,6.5,1);scene.add(glow);
scene.add(new THREE.PointLight(0xffffff,110,0));
scene.add(new THREE.AmbientLight(0x334455,.6));

// planet + orbit line
const ror=P.ror??0.05;
const planet=new THREE.Mesh(new THREE.SphereGeometry(Math.max(ror*starR*4,0.09),32,32),
  new THREE.MeshStandardMaterial({color:P.planetColor,roughness:.7}));
scene.add(planet);
const orbR=4.2;
const oPts=[];for(let i=0;i<=128;i++){const a=i/128*Math.PI*2;
  oPts.push(new THREE.Vector3(orbR*Math.cos(a),0,orbR*Math.sin(a)));}
scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(oPts),
  new THREE.LineBasicMaterial({color:0x3a3f4a,transparent:true,opacity:.8})));

// drag to rotate
let drag=false,lx=0,ly=0;
wrap.addEventListener('pointerdown',e=>{drag=true;lx=e.clientX;ly=e.clientY;});
window.addEventListener('pointerup',()=>drag=false);
window.addEventListener('pointermove',e=>{if(!drag)return;
  az+=(e.clientX-lx)*.008; el=Math.min(1.2,Math.max(.05,el+(e.clientY-ly)*.005));
  lx=e.clientX;ly=e.clientY;placeCam();});

// light curve canvas
const lc=document.getElementById('flux'),lx2=lc.getContext('2d');
function sizeLC(){lc.width=lc.offsetWidth*devicePixelRatio;lc.height=lc.offsetHeight*devicePixelRatio;
  lx2.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);}
sizeLC();
const hist=[];
const orbitSec=P.period?Math.min(14,Math.max(4,3+2.2*Math.log10(1+P.period))):7;
const depthFrac=Math.max(P.depth/1e6,0.02); // exaggerate tiny dips for visibility

function tick(t){
  const a=t/1000/orbitSec*Math.PI*2;
  planet.position.set(orbR*Math.cos(a),0,orbR*Math.sin(a));
  // transit when planet is between camera-side (+z here: use sin>0) and |x|<starR
  const inFront=Math.sin(a)>0&&Math.abs(orbR*Math.cos(a))<starR*1.05;
  const flux=inFront?1-depthFrac:1;
  hist.push(flux);if(hist.length>320)hist.shift();
  // draw
  const w=lc.offsetWidth,h=lc.offsetHeight;
  lx2.clearRect(0,0,w,h);
  lx2.fillStyle='rgba(11,12,16,.72)';lx2.fillRect(0,0,w,h);
  lx2.strokeStyle='rgba(255,255,255,.09)';lx2.strokeRect(0,0,w,h);
  lx2.beginPath();lx2.strokeStyle='#3987e5';lx2.lineWidth=1.8;
  hist.forEach((f,i)=>{const x=i/319*w;
    const y=10+(1-((f-(1-depthFrac*1.3))/(depthFrac*1.5)))*(h-20);
    i?lx2.lineTo(x,y):lx2.moveTo(x,y);});
  lx2.stroke();
  renderer.render(scene,cam);
  requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
</script></body></html>"""
