"""Draw the README diagrams in .github/readme/: pipeline.svg, training-loop.svg, sensor.svg, results.svg.

Each SVG carries its own light and dark colours (``prefers-color-scheme``), so it reads on GitHub in both themes.
The results chart is drawn to scale from the phase 7 reports ``training/runs/phase7-validate/eval/<policy>/<test>.json``
(written by ``run_validate.sh``; not in git, so copy them down with ``cloud/nebius/sync.sh down`` first).
Run from the repository root:  python3 tools/readme_diagrams.py
"""
import json, os
os.makedirs('.github/readme', exist_ok=True)
root='training/runs/phase7-validate/eval'
pol=['nvidia','runB','depth']; tests=['real','fast','harder','flat','straight','moved_box']
vals={p:[json.load(open(f'{root}/{p}/{t}.json'))['summary']['finished_pct'] for t in tests] for p in pol}
print(vals)
STYLE='''<style>
  .bg{fill:#ffffff;stroke:#d0d7de} .ink{fill:#1f2328} .mu{fill:#59636e}
  text{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;font-size:13px}
  .b{font-weight:600} .sm{font-size:11.5px} .hd{font-size:11.5px;font-weight:700;letter-spacing:.06em} .t{font-size:16px;font-weight:700}
  .mac{fill:#fbf0dc;stroke:#9a5b06} .cloud{fill:#e6edf8;stroke:#3b5a8f} .ours{fill:#e1f1ea;stroke:#1d6a57}
  .brain{fill:#f8e6f1;stroke:#9b2f7a} .test{fill:#f0e8fa;stroke:#7046a6} .ext{fill:#eef0ec;stroke:#6a746e} .safe{fill:#f8e4e0;stroke:#a3362a}
  .f-ext{fill:#8a8780} .f-ours{fill:#2a78d6} .f-brain{fill:#1baf7a}
  .l{fill:none;stroke:#59636e;stroke-width:1.6} .lc{fill:none;stroke:#3b5a8f;stroke-width:1.6} .lb{fill:none;stroke:#9b2f7a;stroke-width:1.6} .lt{fill:none;stroke:#7046a6;stroke-width:1.6}
  .grid{stroke:#d0d7de;stroke-width:1} .floor{stroke:#1f2328;stroke-width:2} .dot{fill:#9b2f7a} .hit{fill:#a3362a}
  .m{fill:#59636e} .mc{fill:#3b5a8f} .mb{fill:#9b2f7a} .mt{fill:#7046a6}
  rect,circle{stroke-width:1.5}
  @media (prefers-color-scheme: dark){
    .bg{fill:#0d1117;stroke:#30363d} .ink{fill:#e6edf3} .mu{fill:#9198a1}
    .mac{fill:#2f2310;stroke:#e3a64e} .cloud{fill:#18223a;stroke:#9db5e0} .ours{fill:#132b25;stroke:#62c3a5}
    .brain{fill:#2f1828;stroke:#e895cc} .test{fill:#261d33;stroke:#c2a2ea} .ext{fill:#1c2120;stroke:#95a19b} .safe{fill:#321a17;stroke:#ef8b7e}
    .l{stroke:#9198a1} .lc{stroke:#9db5e0} .lb{stroke:#e895cc} .lt{stroke:#c2a2ea}
    .grid{stroke:#30363d} .floor{stroke:#e6edf3} .dot{fill:#e895cc} .hit{fill:#ef8b7e}
    .m{fill:#9198a1} .mc{fill:#9db5e0} .mb{fill:#e895cc} .mt{fill:#c2a2ea}
  }
</style>
<defs>
  <marker id="am" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="m" d="M0,0 L10,5 L0,10 z"/></marker>
  <marker id="ac" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="mc" d="M0,0 L10,5 L0,10 z"/></marker>
  <marker id="ab" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="mb" d="M0,0 L10,5 L0,10 z"/></marker>
  <marker id="at" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="mt" d="M0,0 L10,5 L0,10 z"/></marker>
</defs>'''
def svg(name,w,h,title,body):
    s=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t">\n<title id="t">{title}</title>\n{STYLE}\n<rect class="bg" x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12"/>\n{body}\n</svg>\n'
    open(f'.github/readme/{name}','w').write(s)
def box(cls,x,y,w,h,title,lines):
    out=[f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="9"/>',f'<text class="ink b" x="{x+14}" y="{y+24}">{title}</text>']
    for i,l in enumerate(lines): out.append(f'<text class="mu sm" x="{x+14}" y="{y+42+i*16}">{l}</text>')
    return '\n'.join(out)

# 1. pipeline
xs=[24,250,476,702]; W=210
b=['<text class="ink t" x="24" y="32">From an idea to a trained duck</text>',
   '<text class="mu sm" x="24" y="50">Claude Code runs every step: FreeCAD and Blender over MCP, the cloud GPU over SSH</text>',
   '<text class="mu hd" x="24" y="80">ON THE MAC</text>']
mac=[("1 · Plan the course",["4 obstacles, sizes, route","concept images (FLUX)"]),
     ("2 · FreeCAD",["exact, parametric shapes","exported as STEP + mesh"]),
     ("3 · Blender",["materials and previews","exported as USD + GLB"]),
     ("4 · Check",["size ±1 mm, metres, Z-up","59 asset + 17 course checks"])]
for i,(t,l) in enumerate(mac):
    b.append(box('mac',xs[i],90,W,74,t,l))
    if i<3: b.append(f'<path class="l" d="M{xs[i]+W} 127 H{xs[i+1]-2}" marker-end="url(#am)"/>')
b.append('<path class="l" d="M807 164 V184 H129 V214" marker-end="url(#am)"/>')
b.append('<text class="mu sm" x="380" y="179">USD files + course manifest</text>')
b.append('<text class="mu hd" x="250" y="206">ON A CLOUD GPU · NEBIUS RTX PRO 6000</text>')
cl=[("cloud","5 · Course in Isaac Lab",["640 lanes as terrain tiles","wet tile with own friction"]),
    ("brain","6 · Train (PPO)",["4,096 ducks in parallel","from NVIDIA's walker"]),
    ("brain","7 · Add eyes",["8 × 8 ToF = 64 inputs","walks round the box itself"]),
    ("test","8 · Final exam",["3 brains × 6 tests","× 128 ducks each"])]
for i,(c,t,l) in enumerate(cl):
    b.append(box(c,xs[i],216,W,74,t,l))
    if i<3: b.append(f'<path class="lc" d="M{xs[i]+W} 253 H{xs[i+1]-2}" marker-end="url(#ac)"/>')
b.append('<path class="lt" d="M807 290 V316" marker-end="url(#at)"/>')
b.append('<rect class="ours" x="24" y="318" width="888" height="46" rx="9"/>')
b.append('<text class="ink b" x="40" y="346">Back on the Mac:</text><text class="mu sm" x="160" y="346">trained policies (.pt) · per-duck scores (JSON) · charts · RTX videos · live Isaac Sim view (WebRTC)</text>')
svg('pipeline.svg',936,384,"The pipeline: plan, FreeCAD, Blender and checks on the Mac; course, training, sensor and exam on a cloud GPU; results back on the Mac.",'\n'.join(b))

# 2. training loop
b=['<text class="ink t" x="24" y="32">How the ducks learn on our course</text>',
   '<text class="mu sm" x="24" y="50">The same loop runs for 4,096 ducks at once, each in its own physics world</text>']
row1=[('cloud',24,210,"Course terrain",["10 difficulty rows × 64 lanes","heights × 0.5–1.5, wet 0.8→0.2"]),
      ('ours',258,200,"Command",["75 %: steer along the route","25 %: NVIDIA's random ones"]),
      ('brain',482,210,"Policy (the brain)",["MLP 512 → 256 → 128","61 or 125 inputs → 14 joints"]),
      ('cloud',716,196,"Newton physics",["MJWarp solver, BAM servos","50 control steps / second"])]
for c,x,w,t,l in row1: b.append(box(c,x,70,w,76,t,l))
for x1,x2,cls,m in ((234,256,'l','am'),(458,480,'lb','ab'),(692,714,'lb','ab')):
    b.append(f'<path class="{cls}" d="M{x1} 108 H{x2}" marker-end="url(#{m})"/>')
b.append(box('test',716,214,196,76,"Reward",["NVIDIA's 15 terms","+ route progress (run B)"]))
b.append('<path class="lc" d="M814 146 V212" marker-end="url(#ac)"/>')
b.append(box('brain',482,214,210,76,"PPO update",["every 24 steps × 4,096 ducks","≈ 1.1 s on the GPU"]))
b.append('<path class="lt" d="M716 252 H694" marker-end="url(#at)"/>')
b.append('<path class="lb" d="M587 214 V148" marker-end="url(#ab)"/>')
b.append(box('test',24,214,210,76,"Checkpoint scored",["every 250 iterations","128 ducks on the real course"]))
b.append('<path class="lb" d="M482 252 H236" marker-end="url(#ab)"/>')
b.append('<text class="mu sm" x="262" y="226">every saved brain is tested,</text><text class="mu sm" x="262" y="242">not just trusted by its reward</text>')
b.append('<text class="mu sm" x="24" y="318">1 iteration = 24 steps × 4,096 ducks = 98,304 duck-steps · 3,000 iterations ≈ 1 hour on one RTX PRO 6000</text>')
svg('training-loop.svg',936,338,"Training loop: course terrain and commands feed the policy, Newton simulates, a reward scores it, PPO updates the policy every 24 steps, and every 250 iterations a checkpoint is scored on the real course.",'\n'.join(b))

# 3. sensor side view (1 m = 450 px, head at x=120, floor y=260, h=0.26 m)
import math
b=['<text class="ink t" x="24" y="32">The duck\'s eyes: an 8 × 8 distance sensor</text>',
   '<text class="mu sm" x="24" y="50">Side view to scale · one ray per row shown (each row has 8 rays across) · 45° × 45° field of view, tilted 30° down</text>']
b.append('<line class="floor" x1="24" y1="260" x2="912" y2="260"/>')
b.append('<rect class="brain" x="96" y="133" width="36" height="22" rx="6"/><rect class="ext" x="104" y="155" width="20" height="105"/>')
b.append('<text class="ink b sm" x="40" y="122">head sensor, 0.26 m up</text>')
hits=[]
for k in range(8):
    a=math.radians(30-22.5+(k+0.5)*45/8)
    x=120+0.26/math.tan(a)*450
    hits.append(round(x,1))
box_x=570; box_top=260-0.15*450
for x in hits:
    if x>box_x:  # blocked by the box: hit where the ray meets x=box_x
        y=143+(box_x-120)*(260-143)/(x-120)
        b.append(f'<path class="lb" d="M120 143 L{box_x} {y:.1f}"/><path class="l" stroke-dasharray="5 4" d="M{box_x} {y:.1f} L{x} 260"/><circle class="hit" cx="{box_x}" cy="{y:.1f}" r="5"/>')
        b.append(f'<text class="mu sm" x="{x}" y="280" text-anchor="middle">floor would be here</text>')
    else:
        b.append(f'<path class="lb" stroke-width="1" d="M120 143 L{x} 260"/><circle class="dot" cx="{x}" cy="260" r="4"/>')
b.append(f'<rect class="ext" x="{box_x}" y="{box_top}" width="90" height="{260-box_top}"/>')
b.append(f'<text class="ink b sm" x="{box_x+45}" y="{box_top-8}" text-anchor="middle">box, 1 m ahead</text>')
b.append(f'<text class="ink sm" x="{box_x+105}" y="214">the top row hits the box: 1.01 m</text><text class="ink sm" x="{box_x+105}" y="232">instead of 1.5 m to the floor</text>')
b.append(f'<text class="mu sm" x="{hits[-1]}" y="280" text-anchor="middle">{0.26/math.tan(math.radians(30+22.5-45/16)):.2f} m</text>')
svg('sensor.svg',936,300,"Side view of the head distance sensor: rays tilted 30 degrees down reach the floor 0.2 to 1.4 m ahead; with a box 1 m ahead, the top row hits the box first.",'\n'.join(b))
print('hits',hits)

# 4. results (bars to scale: height = pct/100 * 220)
names=[("Real course","0.25 m/s"),("Faster","0.35 m/s"),("Harder","heights × 1.4, wet 0.2"),("Flat lanes","forgetting check"),("Straight at box","no steering round it"),("Box moved","never seen there")]
b=['<text class="ink t" x="24" y="32">Final exam: share of 128 ducks that finish</text>']
lx=24
for cls,lab in (('f-ext',"NVIDIA's walker (before)"),('f-ours',"Trained on our course (blind)"),('f-brain',"Trained + head sensor (seeing)")):
    b.append(f'<rect class="{cls}" x="{lx}" y="44" width="14" height="14" rx="3" stroke="none"/><text class="ink sm" x="{lx+20}" y="56">{lab}</text>'); lx+=245
y0,H=300,220
for p in (0,25,50,75,100):
    y=y0-p/100*H; b.append(f'<line class="grid" x1="60" y1="{y}" x2="912" y2="{y}"/><text class="mu sm" x="52" y="{y+4}" text-anchor="end">{p}</text>')
gw=852/6
for g,(n1,n2) in enumerate(names):
    gx=60+g*gw
    for i,(p,cls) in enumerate(zip(pol,('f-ext','f-ours','f-brain'))):
        v=vals[p][g]; h=v/100*H; x=gx+(gw-3*36-2*4)/2+i*40
        b.append(f'<rect class="{cls}" x="{x:.1f}" y="{y0-h:.1f}" width="36" height="{h:.1f}" stroke="none"/>')
        b.append(f'<text class="ink sm" x="{x+18:.1f}" y="{y0-h-5:.1f}" text-anchor="middle">{v:.0f}</text>')
    b.append(f'<text class="ink b sm" x="{gx+gw/2:.1f}" y="{y0+20}" text-anchor="middle">{n1}</text><text class="mu sm" x="{gx+gw/2:.1f}" y="{y0+36}" text-anchor="middle">{n2}</text>')
svg('results.svg',936,356,"Final exam results: percentage of 128 ducks finishing in six tests for NVIDIA's walker, our blind trained walker and our seeing walker.",'\n'.join(b))
