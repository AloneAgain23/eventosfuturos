from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
from datetime import datetime, timedelta
import threading

app = FastAPI(title="CEPLAN Radar de Eventos Futuros")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}
SESSION_TTL_HOURS = 24

def keep_alive():
    import time, urllib.request
    while True:
        try:
            urllib.request.urlopen("https://TU-RADAR-APP.onrender.com/")
        except:
            pass
        time.sleep(840)

threading.Thread(target=keep_alive, daemon=True).start()

def cleanup_sessions():
    now = datetime.utcnow()
    expired = [k for k, v in sessions.items() if v["expires"] < now]
    for k in expired:
        del sessions[k]

@app.get("/")
def root():
    return {"status": "ok", "service": "CEPLAN Radar de Eventos Futuros"}

@app.post("/generateRadar")
async def generate_radar(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Body no es JSON valido")

    titulo = body.get("titulo", "Radar de Eventos Futuros")
    descripcion = body.get("descripcion", "")
    eventos_json = body.get("eventos_json")

    if not eventos_json:
        raise HTTPException(status_code=400, detail="Falta el campo eventos_json")

    if isinstance(eventos_json, str):
        try:
            eventos_json = json.loads(eventos_json)
        except Exception:
            raise HTTPException(status_code=400, detail="eventos_json no es JSON valido")

    cleanup_sessions()

    session_id = str(uuid.uuid4()).replace("-", "")[:16]
    sessions[session_id] = {
        "titulo": titulo,
        "descripcion": descripcion,
        "data": eventos_json,
        "created_at": datetime.utcnow().strftime("%d/%m/%Y"),
        "expires": datetime.utcnow() + timedelta(hours=SESSION_TTL_HOURS),
    }

    BASE_URL = "https://TU-RADAR-APP.onrender.com"
    view_url = f"{BASE_URL}/view/{session_id}"

    return JSONResponse({
        "success": True,
        "view_url": view_url,
        "message": f"Radar listo. Abre: {view_url}",
    })

@app.get("/view/{session_id}", response_class=HTMLResponse)
def view_radar(session_id: str):
    cleanup_sessions()
    if session_id not in sessions:
        return HTMLResponse("""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>No encontrado</title>
<style>body{font-family:sans-serif;display:flex;align-items:center;justify-content:center;
min-height:100vh;background:#f5f5f5;}
.box{text-align:center;padding:3rem;background:#fff;border-radius:12px;
box-shadow:0 4px 24px rgba(0,0,0,.08);max-width:420px;}
h1{color:#C8102E;}p{color:#666;font-size:.9rem;}</style></head>
<body><div class="box"><h1>Sesion no disponible</h1>
<p>Este radar expiro o no existe.<br>Genera uno nuevo desde ChatGPT.</p>
</div></body></html>""", status_code=404)

    s = sessions[session_id]
    data = s["data"]
    eventos = data.get("eventos", [])
    data_json = json.dumps(data, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>{s['titulo']} — CEPLAN</title>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Source+Sans+3:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{{
      --rojo:#C8102E; --rojo-dark:#9B0B22; --gris:#F4F5F6;
      --borde:#DDE1E6; --texto:#111827; --muted:#6B7280; --blanco:#FFFFFF;
      --social:#2E86AB; --tecnologico:#A23B72; --economico:#F18F01;
      --ambiental:#3BB273; --politico:#E84855;
      --sd:#60A5FA; --rd:#FBBF24; --cs:#F87171; --ec:#A78BFA;
    }}
    *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
    body{{background:var(--gris);color:var(--texto);font-family:'Source Sans 3',sans-serif;font-size:15px;}}
    header{{background:var(--rojo);box-shadow:0 2px 16px rgba(200,16,46,.35);position:sticky;top:0;z-index:100;}}
    .hi{{max-width:1400px;margin:0 auto;padding:.85rem 2rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;}}
    .hb{{font-weight:700;font-size:.95rem;text-transform:uppercase;letter-spacing:.06em;color:#fff;}}
    .hb span{{display:block;font-size:.6rem;font-weight:400;opacity:.75;letter-spacing:.12em;}}
    .hbadge{{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.3);border-radius:4px;padding:.28rem .75rem;font-size:.7rem;font-weight:600;color:#fff;}}

    .hero{{background:var(--blanco);border-bottom:4px solid var(--rojo);padding:1.5rem 2rem;}}
    .hero-inner{{max-width:1400px;margin:0 auto;}}
    .eyebrow{{font-size:.68rem;font-weight:700;letter-spacing:.2em;text-transform:uppercase;color:var(--rojo);margin-bottom:.3rem;}}
    .hero-title{{font-family:'Playfair Display',serif;font-size:clamp(1.4rem,3vw,2.2rem);font-weight:700;color:var(--texto);line-height:1.2;}}
    .hero-desc{{font-size:.88rem;color:var(--muted);margin-top:.4rem;max-width:700px;}}

    .main{{max-width:1400px;margin:0 auto;padding:1.5rem 2rem 3rem;display:grid;grid-template-columns:1fr 340px;gap:1.5rem;}}
    @media(max-width:1024px){{.main{{grid-template-columns:1fr;}}}}

    /* FILTERS */
    .filters{{background:var(--blanco);border:1px solid var(--borde);border-radius:8px;padding:1.2rem;margin-bottom:1.5rem;display:flex;flex-wrap:wrap;gap:1rem;align-items:center;}}
    .filter-group{{display:flex;flex-wrap:wrap;gap:.4rem;align-items:center;}}
    .filter-label{{font-size:.65rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-right:.2rem;}}
    .fbtn{{font-size:.7rem;font-weight:700;padding:.28rem .75rem;border-radius:4px;border:1.5px solid var(--borde);background:var(--blanco);color:var(--muted);cursor:pointer;text-transform:uppercase;letter-spacing:.06em;transition:all .14s;}}
    .fbtn:hover{{border-color:var(--rojo);color:var(--rojo);}}
    .fbtn.active{{color:#fff;border-color:currentColor;}}
    .fbtn.all.active{{background:var(--rojo);border-color:var(--rojo);}}
    .fbtn.social.active{{background:var(--social);border-color:var(--social);}}
    .fbtn.tecnologico.active{{background:var(--tecnologico);border-color:var(--tecnologico);}}
    .fbtn.economico.active{{background:var(--economico);border-color:var(--economico);}}
    .fbtn.ambiental.active{{background:var(--ambiental);border-color:var(--ambiental);}}
    .fbtn.politico.active{{background:var(--politico);border-color:var(--politico);}}
    .fbtn.sd.active{{background:var(--sd);border-color:var(--sd);color:#111;}}
    .fbtn.rd.active{{background:var(--rd);border-color:var(--rd);color:#111;}}
    .fbtn.cs.active{{background:var(--cs);border-color:var(--cs);}}
    .fbtn.ec.active{{background:var(--ec);border-color:var(--ec);}}

    /* RADAR */
    .radar-wrap{{background:var(--blanco);border:1px solid var(--borde);border-radius:12px;padding:1.5rem;display:flex;justify-content:center;align-items:center;min-height:600px;position:relative;}}
    #radar-svg{{max-width:100%;height:auto;}}

    /* LEGEND */
    .legend{{background:var(--blanco);border:1px solid var(--borde);border-radius:8px;padding:1.2rem;}}
    .legend-title{{font-size:.7rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.8rem;}}
    .legend-section{{margin-bottom:1rem;}}
    .legend-section-label{{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.4rem;}}
    .legend-item{{display:flex;align-items:center;gap:.5rem;margin-bottom:.35rem;font-size:.82rem;color:var(--texto);}}
    .legend-dot{{width:12px;height:12px;border-radius:50%;flex-shrink:0;}}
    .legend-sq{{width:12px;height:12px;border-radius:2px;flex-shrink:0;}}

    /* STATS */
    .stats-bar{{display:flex;flex-wrap:wrap;gap:.6rem;margin-bottom:1.2rem;}}
    .stat{{background:var(--blanco);border:1px solid var(--borde);border-top:3px solid var(--rojo);border-radius:6px;padding:.7rem 1rem;flex:1;min-width:80px;}}
    .stat-num{{font-family:'Playfair Display',serif;font-size:1.6rem;font-weight:700;color:var(--rojo);line-height:1;}}
    .stat-label{{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-top:.1rem;}}

    /* POPUP */
    .popup-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:200;align-items:center;justify-content:center;padding:1rem;}}
    .popup-overlay.open{{display:flex;}}
    .popup{{background:var(--blanco);border-radius:12px;max-width:520px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 60px rgba(0,0,0,.3);animation:popIn .2s ease;}}
    @keyframes popIn{{from{{opacity:0;transform:scale(.95);}}to{{opacity:1;transform:scale(1);}}}}
    .popup-header{{padding:1.2rem 1.5rem;border-bottom:1px solid var(--borde);display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;}}
    .popup-tipo{{font-size:.62rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;padding:.2rem .6rem;border-radius:3px;display:inline-block;margin-bottom:.4rem;}}
    .popup-nombre{{font-family:'Playfair Display',serif;font-size:1.1rem;font-weight:700;color:var(--texto);line-height:1.3;}}
    .popup-close{{background:none;border:none;font-size:1.3rem;cursor:pointer;color:var(--muted);padding:.2rem;line-height:1;flex-shrink:0;}}
    .popup-close:hover{{color:var(--rojo);}}
    .popup-body{{padding:1.2rem 1.5rem;}}
    .popup-desc{{font-size:.9rem;line-height:1.75;color:var(--texto);margin-bottom:1.2rem;}}
    .popup-chips{{display:flex;flex-wrap:wrap;gap:.4rem;margin-bottom:1.2rem;}}
    .popup-chip{{font-size:.68rem;font-weight:700;padding:.2rem .6rem;border-radius:12px;border:1px solid var(--borde);color:var(--muted);background:var(--gris);}}
    .popup-grid{{display:grid;grid-template-columns:1fr 1fr;gap:.8rem;margin-bottom:1rem;}}
    .popup-metric{{background:var(--gris);border-radius:6px;padding:.7rem .9rem;}}
    .popup-metric-label{{font-size:.6rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:.3rem;}}
    .popup-metric-value{{font-size:.85rem;font-weight:600;color:var(--texto);}}
    .popup-bar{{height:6px;background:var(--borde);border-radius:3px;margin-top:.4rem;overflow:hidden;}}
    .popup-bar-fill{{height:100%;border-radius:3px;transition:width .3s;}}
    .popup-fuente{{font-size:.75rem;color:var(--muted);font-style:italic;border-top:1px solid var(--borde);padding-top:.8rem;margin-top:.5rem;}}

    footer{{background:var(--rojo-dark,#9B0B22);color:rgba(255,255,255,.7);padding:1rem 2rem;text-align:center;font-size:.68rem;letter-spacing:.06em;}}
    @media(max-width:640px){{.main{{padding:1rem;}} .hero{{padding:1rem;}} .hi{{padding:.8rem 1rem;}}}}
  </style>
</head>
<body>
<header>
  <div class="hi">
    <div class="hb">Radar de Eventos Futuros<span>CEPLAN — Centro Nacional de Planeamiento Estrategico</span></div>
    <div class="hbadge">Peru al 2050 · STEEP</div>
  </div>
</header>

<div class="hero">
  <div class="hero-inner">
    <div class="eyebrow">&#9656; Vigilancia del horizonte</div>
    <h1 class="hero-title">{s['titulo']}</h1>
    {"<p class='hero-desc'>" + s['descripcion'] + "</p>" if s['descripcion'] else ""}
  </div>
</div>

<div style="max-width:1400px;margin:1.5rem auto 0;padding:0 2rem;">
  <div class="stats-bar" id="statsBar"></div>
  <div class="filters" id="filterBar">
    <div class="filter-group">
      <span class="filter-label">Tematica:</span>
      <button class="fbtn all active" data-steep="all">Todas</button>
      <button class="fbtn social" data-steep="Social">Social</button>
      <button class="fbtn tecnologico" data-steep="Tecnologico">Tecnol.</button>
      <button class="fbtn economico" data-steep="Economico">Econ.</button>
      <button class="fbtn ambiental" data-steep="Ambiental">Ambient.</button>
      <button class="fbtn politico" data-steep="Politico">Politico</button>
    </div>
    <div class="filter-group">
      <span class="filter-label">Tipo:</span>
      <button class="fbtn all active" data-tipo="all">Todos</button>
      <button class="fbtn sd" data-tipo="SD">SD</button>
      <button class="fbtn rd" data-tipo="RD">RD</button>
      <button class="fbtn cs" data-tipo="CS">CS</button>
      <button class="fbtn ec" data-tipo="EC">EC</button>
    </div>
  </div>
</div>

<div class="main">
  <div>
    <div class="radar-wrap">
      <svg id="radar-svg" viewBox="0 0 700 700" xmlns="http://www.w3.org/2000/svg"></svg>
    </div>
    <p style="text-align:center;font-size:.72rem;color:var(--muted);margin-top:.6rem;">Haz click en cualquier evento para ver los detalles</p>
  </div>
  <div class="legend" id="legend">
    <div class="legend-title">Leyenda</div>
    <div class="legend-section">
      <div class="legend-section-label">Plazo</div>
      <div class="legend-item"><div style="width:28px;height:12px;border-radius:6px;background:rgba(200,16,46,.15);border:2px solid rgba(200,16,46,.4);"></div> Corto (hasta 2035)</div>
      <div class="legend-item"><div style="width:28px;height:12px;border-radius:6px;background:rgba(200,16,46,.08);border:2px solid rgba(200,16,46,.25);"></div> Mediano (hasta 2045)</div>
      <div class="legend-item"><div style="width:28px;height:12px;border-radius:6px;background:rgba(200,16,46,.03);border:2px solid rgba(200,16,46,.12);"></div> Largo (hasta 2050)</div>
    </div>
    <div class="legend-section">
      <div class="legend-section-label">Tipo de evento</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--sd);"></div> SD — Señal debil</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--rd);"></div> RD — Ruptura/Disrupcion</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--cs);"></div> CS — Carta salvaje</div>
      <div class="legend-item"><div class="legend-dot" style="background:var(--ec);"></div> EC — Evento catastrofico</div>
    </div>
    <div class="legend-section">
      <div class="legend-section-label">Tematica STEEP</div>
      <div class="legend-item"><div class="legend-sq" style="background:var(--social);"></div> Social</div>
      <div class="legend-item"><div class="legend-sq" style="background:var(--tecnologico);"></div> Tecnologico</div>
      <div class="legend-item"><div class="legend-sq" style="background:var(--economico);"></div> Economico</div>
      <div class="legend-item"><div class="legend-sq" style="background:var(--ambiental);"></div> Ambiental</div>
      <div class="legend-item"><div class="legend-sq" style="background:var(--politico);"></div> Politico</div>
    </div>
  </div>
</div>

<!-- POPUP -->
<div class="popup-overlay" id="popupOverlay">
  <div class="popup" id="popup">
    <div class="popup-header">
      <div>
        <div class="popup-tipo" id="popupTipo"></div>
        <div class="popup-nombre" id="popupNombre"></div>
      </div>
      <button class="popup-close" id="popupClose">&#10005;</button>
    </div>
    <div class="popup-body">
      <p class="popup-desc" id="popupDesc"></p>
      <div class="popup-chips" id="popupChips"></div>
      <div class="popup-grid" id="popupGrid"></div>
      <div class="popup-fuente" id="popupFuente"></div>
    </div>
  </div>
</div>

<footer>CEPLAN — Centro Nacional de Planeamiento Estrategico &nbsp;|&nbsp; {s['created_at']} &nbsp;|&nbsp; Radar de Eventos Futuros · Peru al 2050 · Sesion valida 24h</footer>

<script>
const DATA = {data_json};
const eventos = DATA.eventos || [];

// COLORS
const STEEP_COLOR = {{
  'Social':'#2E86AB','Tecnologico':'#A23B72','Economico':'#F18F01',
  'Ambiental':'#3BB273','Politico':'#E84855'
}};
const TIPO_COLOR = {{'SD':'#60A5FA','RD':'#FBBF24','CS':'#F87171','EC':'#A78BFA'}};
const TIPO_LABEL = {{'SD':'Señal Debil','RD':'Ruptura/Disrupcion','CS':'Carta Salvaje','EC':'Evento Catastrofico'}};
const PLAZO_RING = {{'corto':1,'mediano':2,'largo':3}};

// STATS
(function(){{
  const bar = document.getElementById('statsBar');
  const tipos = {{}};
  eventos.forEach(e=>{{ tipos[e.tipo]=(tipos[e.tipo]||0)+1; }});
  [[eventos.length,'Total'],['SD','Señales Debiles'],['RD','Disrupciones'],['CS','Cartas Salvajes'],['EC','Catastroficos']].forEach(([k,l])=>{{
    const n = typeof k==='number'?k:(tipos[k]||0);
    const d=document.createElement('div'); d.className='stat';
    d.innerHTML=`<div class="stat-num">${{n}}</div><div class="stat-label">${{l}}</div>`;
    bar.appendChild(d);
  }});
}})();

// RADAR DRAW
const SVG_NS = 'http://www.w3.org/2000/svg';
const svg = document.getElementById('radar-svg');
const CX=350, CY=350;
const RINGS=[140,240,320]; // radii for corto, mediano, largo
const STEEP_SECTORS=['Social','Tecnologico','Economico','Ambiental','Politico'];
const SECTOR_ANGLE = 360/5;

let activeSTEEP='all', activeTIPO='all';

function polarToCart(cx,cy,r,angleDeg){{
  const rad=(angleDeg-90)*Math.PI/180;
  return [cx+r*Math.cos(rad), cy+r*Math.sin(rad)];
}}

function drawRadar(filteredEvts){{
  svg.innerHTML='';

  // Background rings
  RINGS.forEach((r,i)=>{{
    const opacity=[0.15,0.08,0.03][i];
    const strokeOp=[0.4,0.25,0.12][i];
    const circle=document.createElementNS(SVG_NS,'circle');
    circle.setAttribute('cx',CX); circle.setAttribute('cy',CY);
    circle.setAttribute('r',r);
    circle.setAttribute('fill',`rgba(200,16,46,${{opacity}})`);
    circle.setAttribute('stroke',`rgba(200,16,46,${{strokeOp}})`);
    circle.setAttribute('stroke-width','1.5');
    svg.appendChild(circle);
  }});

  // Outer circle border
  const outer=document.createElementNS(SVG_NS,'circle');
  outer.setAttribute('cx',CX);outer.setAttribute('cy',CY);outer.setAttribute('r',340);
  outer.setAttribute('fill','none');outer.setAttribute('stroke','rgba(200,16,46,0.08)');outer.setAttribute('stroke-width','1');
  svg.appendChild(outer);

  // Sector dividers & labels
  STEEP_SECTORS.forEach((s,i)=>{{
    const angle=i*SECTOR_ANGLE;
    const [x1,y1]=polarToCart(CX,CY,0,angle);
    const [x2,y2]=polarToCart(CX,CY,340,angle);
    const line=document.createElementNS(SVG_NS,'line');
    line.setAttribute('x1',CX);line.setAttribute('y1',CY);
    line.setAttribute('x2',x2);line.setAttribute('y2',y2);
    line.setAttribute('stroke','rgba(200,16,46,0.12)');line.setAttribute('stroke-width','1');
    svg.appendChild(line);

    // Sector label
    const labelAngle=angle+SECTOR_ANGLE/2;
    const [lx,ly]=polarToCart(CX,CY,360,labelAngle);
    const text=document.createElementNS(SVG_NS,'text');
    text.setAttribute('x',lx);text.setAttribute('y',ly);
    text.setAttribute('text-anchor','middle');text.setAttribute('dominant-baseline','middle');
    text.setAttribute('font-size','11');text.setAttribute('font-weight','700');
    text.setAttribute('font-family','Source Sans 3, sans-serif');
    text.setAttribute('fill',STEEP_COLOR[s]);
    text.setAttribute('letter-spacing','0.08em');
    text.textContent=s.toUpperCase();
    svg.appendChild(text);
  }});

  // Ring labels
  [['CORTO',RINGS[0]],['MEDIANO',RINGS[1]],['LARGO',RINGS[2]]].forEach(([label,r])=>{{
    const text=document.createElementNS(SVG_NS,'text');
    text.setAttribute('x',CX);text.setAttribute('y',CY-r+14);
    text.setAttribute('text-anchor','middle');text.setAttribute('font-size','9');
    text.setAttribute('font-family','Source Sans 3, sans-serif');
    text.setAttribute('fill','rgba(200,16,46,0.5)');text.setAttribute('font-weight','700');
    text.setAttribute('letter-spacing','0.15em');
    text.textContent=label;
    svg.appendChild(text);
  }});

  // Center globe icon
  const globe=document.createElementNS(SVG_NS,'circle');
  globe.setAttribute('cx',CX);globe.setAttribute('cy',CY);globe.setAttribute('r',22);
  globe.setAttribute('fill','#C8102E');globe.setAttribute('opacity','0.15');
  svg.appendChild(globe);
  const globeT=document.createElementNS(SVG_NS,'text');
  globeT.setAttribute('x',CX);globeT.setAttribute('y',CY+1);
  globeT.setAttribute('text-anchor','middle');globeT.setAttribute('dominant-baseline','middle');
  globeT.setAttribute('font-size','20');globeT.textContent='🌐';
  svg.appendChild(globeT);

  // Plot events
  // Group events by sector to distribute angularly within each sector
  const bySector={{}};
  filteredEvts.forEach(e=>{{
    const sec=e.tematica||'Social';
    if(!bySector[sec]) bySector[sec]=[];
    bySector[sec].push(e);
  }});

  filteredEvts.forEach(e=>{{
    const sectorIdx=STEEP_SECTORS.indexOf(e.tematica||'Social');
    if(sectorIdx<0) return;
    const sectorEvts=bySector[e.tematica];
    const eIdx=sectorEvts.indexOf(e);
    const total=sectorEvts.length;

    const baseAngle=sectorIdx*SECTOR_ANGLE;
    const padding=SECTOR_ANGLE*0.12;
    const spread=SECTOR_ANGLE-padding*2;
    const angleOffset = total>1 ? padding+spread*(eIdx/(total-1)) : SECTOR_ANGLE/2;
    const angle=baseAngle+angleOffset;

    const ring=PLAZO_RING[e.plazo]||1;
    const rInner=ring===1?30:RINGS[ring-2]+15;
    const rOuter=RINGS[ring-1]-15;
    const r=rInner+(rOuter-rInner)*0.5+(Math.random()-0.5)*(rOuter-rInner)*0.3;
    const [px,py]=polarToCart(CX,CY,Math.max(rInner+8,r),angle);

    const tipoCo=TIPO_COLOR[e.tipo]||'#999';
    const steepCo=STEEP_COLOR[e.tematica]||'#999';

    // Outer ring (STEEP color)
    const outerC=document.createElementNS(SVG_NS,'circle');
    outerC.setAttribute('cx',px);outerC.setAttribute('cy',py);outerC.setAttribute('r','13');
    outerC.setAttribute('fill',steepCo);outerC.setAttribute('opacity','0.25');
    outerC.style.cursor='pointer';
    svg.appendChild(outerC);

    // Inner dot (tipo color)
    const dot=document.createElementNS(SVG_NS,'circle');
    dot.setAttribute('cx',px);dot.setAttribute('cy',py);dot.setAttribute('r','8');
    dot.setAttribute('fill',tipoCo);dot.setAttribute('stroke','#fff');dot.setAttribute('stroke-width','1.5');
    dot.style.cursor='pointer';
    dot.setAttribute('data-id',e.id||'');
    svg.appendChild(dot);

    // Tipo label inside dot
    const tipeTxt=document.createElementNS(SVG_NS,'text');
    tipeTxt.setAttribute('x',px);tipeTxt.setAttribute('y',py+1);
    tipeTxt.setAttribute('text-anchor','middle');tipeTxt.setAttribute('dominant-baseline','middle');
    tipeTxt.setAttribute('font-size','5.5');tipeTxt.setAttribute('font-weight','700');
    tipeTxt.setAttribute('fill','#fff');tipeTxt.setAttribute('font-family','Source Sans 3,sans-serif');
    tipeTxt.textContent=e.tipo||'';
    tipeTxt.style.cursor='pointer';
    svg.appendChild(tipeTxt);

    // Hover group for click
    [outerC,dot,tipeTxt].forEach(el=>{{
      el.addEventListener('click',()=>openPopup(e));
      el.addEventListener('mouseenter',()=>{{dot.setAttribute('r','10');outerC.setAttribute('r','15');}});
      el.addEventListener('mouseleave',()=>{{dot.setAttribute('r','8');outerC.setAttribute('r','13');}});
    }});

    // Short name label
    const nameWords=(e.nombre||'').split(' ');
    const shortName=nameWords.slice(0,2).join(' ')+(nameWords.length>2?'…':'');
    const lbl=document.createElementNS(SVG_NS,'text');
    lbl.setAttribute('x',px);lbl.setAttribute('y',py+20);
    lbl.setAttribute('text-anchor','middle');lbl.setAttribute('font-size','8');
    lbl.setAttribute('font-family','Source Sans 3,sans-serif');
    lbl.setAttribute('fill','var(--texto)');lbl.setAttribute('font-weight','600');
    lbl.style.cursor='pointer';
    lbl.textContent=shortName;
    lbl.addEventListener('click',()=>openPopup(e));
    svg.appendChild(lbl);
  }});
}}

// POPUP
function openPopup(e){{
  const tipoCo=TIPO_COLOR[e.tipo]||'#999';
  const steepCo=STEEP_COLOR[e.tematica]||'#999';

  document.getElementById('popupTipo').textContent=(TIPO_LABEL[e.tipo]||e.tipo)+' ('+e.tipo+')';
  document.getElementById('popupTipo').style.background=tipoCo+'22';
  document.getElementById('popupTipo').style.color=tipoCo;
  document.getElementById('popupNombre').textContent=e.nombre||'';
  document.getElementById('popupDesc').textContent=e.descripcion||'';

  const chips=document.getElementById('popupChips');
  chips.innerHTML='';
  [
    [e.tematica,'background:'+steepCo+'22;color:'+steepCo],
    [e.plazo?e.plazo.charAt(0).toUpperCase()+e.plazo.slice(1)+' plazo':'',''],
    [e.plazo==='corto'?'Hasta 2035':e.plazo==='mediano'?'Hasta 2045':'Hasta 2050',''],
  ].filter(([t])=>t).forEach(([t,st])=>{{
    const c=document.createElement('span');
    c.className='popup-chip';c.textContent=t;
    if(st)c.style.cssText=st;
    chips.appendChild(c);
  }});

  const grid=document.getElementById('popupGrid');
  grid.innerHTML='';

  // Anticipacion
  const antVal=e.nivel_anticipacion||5;
  const antColor=antVal>=7?'#3BB273':antVal>=4?'#F18F01':'#E84855';
  grid.innerHTML+=`
    <div class="popup-metric">
      <div class="popup-metric-label">Nivel de Anticipacion</div>
      <div class="popup-metric-value" style="color:${{antColor}}">${{antVal}}/10 — ${{antVal>=7?'Alto':antVal>=4?'Medio':'Bajo'}}</div>
      <div class="popup-bar"><div class="popup-bar-fill" style="width:${{antVal*10}}%;background:${{antColor}}"></div></div>
    </div>`;

  // Impacto
  const impVal=e.nivel_impacto||5;
  const impColor=impVal>=7?'#E84855':impVal>=4?'#F18F01':'#3BB273';
  grid.innerHTML+=`
    <div class="popup-metric">
      <div class="popup-metric-label">Impacto en el Peru</div>
      <div class="popup-metric-value" style="color:${{impColor}}">${{impVal}}/10 — ${{impVal>=7?'Alto':impVal>=4?'Medio':'Bajo'}}</div>
      <div class="popup-bar"><div class="popup-bar-fill" style="width:${{impVal*10}}%;background:${{impColor}}"></div></div>
    </div>`;

  // Caracteristicas clave
  if(e.caracteristicas&&e.caracteristicas.length){{
    const ul=document.createElement('div');
    ul.style.cssText='grid-column:1/-1;background:var(--gris);border-radius:6px;padding:.7rem .9rem;';
    ul.innerHTML='<div class="popup-metric-label">Caracteristicas clave</div>'
      +e.caracteristicas.map(c=>`<div style="font-size:.83rem;padding:.2rem 0;border-bottom:1px solid var(--borde);color:var(--texto);">▸ ${{c}}</div>`).join('');
    grid.appendChild(ul);
  }}

  const fuente=document.getElementById('popupFuente');
  fuente.textContent=e.fuente?'Fuente: '+e.fuente:'';
  fuente.style.display=e.fuente?'block':'none';

  document.getElementById('popupOverlay').classList.add('open');
}}

document.getElementById('popupClose').addEventListener('click',()=>{{
  document.getElementById('popupOverlay').classList.remove('open');
}});
document.getElementById('popupOverlay').addEventListener('click',function(e){{
  if(e.target===this) this.classList.remove('open');
}});

// FILTERS
function getFiltered(){{
  return eventos.filter(e=>{{
    const steepOk=activeSTEEP==='all'||(e.tematica||'')===activeSTEEP;
    const tipoOk=activeTIPO==='all'||(e.tipo||'')===activeTIPO;
    return steepOk&&tipoOk;
  }});
}}

document.querySelectorAll('[data-steep]').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('[data-steep]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    activeSTEEP=btn.dataset.steep;
    drawRadar(getFiltered());
  }});
}});

document.querySelectorAll('[data-tipo]').forEach(btn=>{{
  btn.addEventListener('click',()=>{{
    document.querySelectorAll('[data-tipo]').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    activeTIPO=btn.dataset.tipo;
    drawRadar(getFiltered());
  }});
}});

// Initial draw
drawRadar(eventos);
</script>
</body>
</html>"""
    return HTMLResponse(html)
