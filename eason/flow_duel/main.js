// 外資連賣10天，台股卻漲？— 11/27, riddle + character duel, dark hand-drawn, 1080×1920, 23.5 s
// Data: TWSE BFI82U (11/16–11/27, Nov 1–27), FMTQIK (TAIEX 11/25–11/27); 內政部 10 月底人口 2320.4 萬.
import * as E from './engine.js';
const { P } = E;
Object.assign(P, { paper: '#14161B', dotgrid: '#2A2E36', ink: '#ECE6DA', inkSoft: '#8F897F', rule: '#3A3E46', graphite: '#ECE6DA' });
const cv = document.getElementById('c'), g = cv.getContext('2d');
const HAND = 'Caveat, WenKai', SERIF = 'Newsreader, "Noto Serif CJK TC"', MONO = '"IBM Plex Mono", "Noto Sans CJK TC"', SANS = '"Noto Sans CJK TC"';
await Promise.all(['500 40px Caveat', '400 40px Newsreader', '400 20px "IBM Plex Mono"', '700 40px "Noto Serif CJK TC"', '900 40px "Noto Sans CJK TC"', '500 40px WenKai', '700 40px WenKai'].map(f => document.fonts.load(f, '外資投信買賣台積電萬億')));

const SELL10 = 5004.7, NOV = 11216.4, PER = 48338, F2 = 788.1, IT2 = 297.3;
const IDX = [['11/25', 38195.43], ['11/26', 39151.81], ['11/27', 39308.08]];
const DAYS10 = [-701.9, -380.9, -765.6, -243.1, -95.1, -289.5, -503.9, -1236.5, -491.8, -296.3];
const RED = '#FF6B61', GREEN = '#4FC07E', HI = '#F2C14E', NAVY = '#2B3A55', GREY = '#9AA0A8', ORANGE = '#E8954A', BLUE = '#5B8FD6';

const LINES = [
  { t: [0.0, 2.5], txt: ['外資連賣十天，', '賣掉五千億'] },
  { t: [2.8, 5.7], txt: ['台股這兩天，', '卻漲了一千一百點'] },
  { t: [6.0, 7.7], txt: ['錢到底是誰在接？'] },
  { t: [8.1, 12.7], txt: ['外資這個月搬走的錢，', '平均到每個台灣人，', '一人四萬八'] },
  { t: [13.1, 15.0], txt: ['法人裡面，', '在下面接的是投信'] },
  { t: [15.3, 18.8], txt: ['外資兩天賣七百多億，', '投信接了快三百億'] },
  { t: [19.2, 21.7], txt: ['外資還會賣幾天？', '留言猜猜看'] },
];
const DUR = 23.5;
const cl = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const ph = (t, a, b) => cl((t - a) / (b - a));
const easeO = u => 1 - Math.pow(1 - u, 3), easeIO = u => u < .5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;
const mix = (a, b, u) => a + (b - a) * u;
const fmt = n => Math.round(n).toLocaleString('en-US');
function ctext(s, x, y, font, color, a = 1, align = 'center') { g.save(); g.font = font; g.textAlign = align; g.fillStyle = color; g.globalAlpha *= a; g.fillText(s, x, y); g.restore(); }
const circle = (x, y, r, n = 36) => Array.from({ length: n + 1 }, (_, i) => [x + Math.cos(i / n * 6.2832) * r, y + Math.sin(i / n * 6.2832) * r]);

// ---------- pencil-drawn cats ----------
// kind 'fii' grey cat, navy suit, sunglasses, red tie; 'it' orange cat, white shirt, suspenders, blue badge.
function cat(kind, x, y, s, prog, t, pose = 0) {
  let tip = null;
  const st = (pts, col, w, a, b, seed) => { const u = ph(prog, a, b); if (u <= 0) return; const p = E.pencilStroke(g, pts, { color: col, width: w * s, progress: u, seed }); if (u < 1) tip = p; };
  const fur = kind === 'fii' ? GREY : ORANGE, cloth = kind === 'fii' ? NAVY : '#EDEDE8';
  const bob = Math.sin(t * 5 + (kind === 'fii' ? 0 : 1.7)) * 4 * s;
  g.save(); g.translate(x, y + bob); g.scale(s, s);
  const f = ph(prog, .55, .8);                                   // fills arrive after the outline
  if (f > 0) {
    g.globalAlpha = f;
    E.inkShape(g, [[-70, 60], [70, 60], [90, 210], [-90, 210]], { fill: cloth, hatch: .3, seed: 3, width: 0, stroke: 'rgba(0,0,0,0)' });
    E.inkShape(g, circle(0, 0, 72), { fill: fur, hatch: .35, seed: 5, width: 0, stroke: 'rgba(0,0,0,0)' });
    E.inkShape(g, [[-64, -38], [-50, -100], [-18, -62]], { fill: fur, hatch: .3, seed: 6, width: 0, stroke: 'rgba(0,0,0,0)' });
    E.inkShape(g, [[64, -38], [50, -100], [18, -62]], { fill: fur, hatch: .3, seed: 7, width: 0, stroke: 'rgba(0,0,0,0)' });
    g.globalAlpha = 1;
  }
  g.restore();
  // outlines (in world space so the pencil tip is trackable)
  const T = pts => pts.map(([px, py]) => [x + px * s, y + bob + py * s]);
  st(T(circle(0, 0, 72)), P.ink, 3, 0, .25, 11);
  st(T([[-64, -38], [-50, -100], [-18, -62]]), P.ink, 3, .22, .3, 12);
  st(T([[64, -38], [50, -100], [18, -62]]), P.ink, 3, .3, .38, 13);
  st(T([[-70, 60], [-90, 210]]), P.ink, 3, .38, .45, 14);
  st(T([[70, 60], [90, 210]]), P.ink, 3, .45, .52, 15);
  if (kind === 'fii') {
    st(T([[-52, -12], [-10, -12], [-12, 12], [-50, 12], [-52, -12]]), '#0C0D10', 6, .5, .58, 16);
    st(T([[10, -12], [52, -12], [50, 12], [12, 12], [10, -12]]), '#0C0D10', 6, .56, .64, 17);
    st(T([[-10, -6], [10, -6]]), '#0C0D10', 4, .63, .66, 18);
    if (prog > .66) { g.save(); g.fillStyle = '#0C0D10'; for (const ex of [-31, 31]) { g.beginPath(); g.ellipse(x + ex * s, y + bob, 19 * s, 11 * s, 0, 0, 7); g.fill(); } g.restore(); }
    st(T([[0, 64], [-12, 82], [0, 150], [12, 82], [0, 64]]), RED, 6, .66, .75, 19);
  } else {
    for (const ex of [-26, 26]) if (prog > .6) { g.save(); g.fillStyle = '#16120E'; g.beginPath(); g.arc(x + ex * s, y + bob - 4 * s, 8 * s, 0, 7); g.fill(); g.restore(); }
    st(T([[-40, 64], [-50, 210]]), '#16120E', 5, .62, .68, 20);
    st(T([[40, 64], [50, 210]]), '#16120E', 5, .68, .74, 21);
    st(T([[-26, 110], [26, 110], [26, 150], [-26, 150], [-26, 110]]), BLUE, 5, .74, .8, 22);
  }
  st(T([[-14, 30], [0, 38], [14, 30]]), P.ink, 3, .78, .82, 23);           // mouth
  st(T([[-40, 24], [-100, 18]]), P.ink, 2, .82, .85, 24); st(T([[40, 24], [100, 18]]), P.ink, 2, .85, .88, 25);
  return tip;
}
function bag(x, y, s, label) {                                   // a money bag
  E.inkShape(g, circle(x, y, 30 * s, 20), { fill: HI, hatch: .3, seed: 61, width: 2 });
  E.pencilStroke(g, [[x - 12 * s, y - 30 * s], [x, y - 44 * s], [x + 12 * s, y - 30 * s]], { color: P.ink, width: 2.4, seed: 62 });
  ctext(label, x, y + 11 * s, `900 ${30 * s}px ${SANS}`, '#2A1E05');
}

let probe = false, probeTip = null;
function render(t) {
  let sx = 0, sy = 0;
  for (const [ts, a0] of [[0.3, 20], [6.5, 26], [10.9, 14]]) if (t > ts) { const d = t - ts, a = a0 * Math.exp(-d * 7); sx += a * Math.sin(d * 61); sy += a * Math.cos(d * 47); }
  const cam = { x: 0, y: 0, zoom: 1 + .03 * Math.exp(-Math.max(0, t - .3) * 5) * (t > .3), roll: 0, sx, sy };
  g.setTransform(1, 0, 0, 1, 0, 0); g.fillStyle = P.paper; g.fillRect(0, 0, 1080, 1920);
  E.applyCam(g, cam);
  g.fillStyle = P.dotgrid; for (let x = -600; x <= 600; x += 28) for (let y = -1000; y <= 1000; y += 28) g.fillRect(x - 1.2, y - 1.2, 2.4, 2.4);
  let tip = null, flip = 0; const track = (p, f) => { if (p) { tip = p; flip = f; } };

  // fixed promise line
  E.setType(g, '外資連賣 10 天，', -430, -790, { size: 70, font: SERIF, weight: 700, color: GREEN, progress: ph(t, 0, .35) });
  E.setType(g, '台股卻漲？', 110, -790, { size: 70, font: SERIF, weight: 700, color: RED, progress: ph(t, .2, .5) });
  E.setType(g, '11/27 盤後｜證交所', -430, -860, { size: 24, font: MONO, color: P.inkSoft, progress: ph(t, .3, .8) });
  E.setType(g, '股市壹神指標學', 430, 860, { size: 26, font: MONO, color: P.inkSoft, align: 'right', progress: ph(t, .8, 1.4) });

  // ===== Act 1 (0–8): split screen riddle =====
  const a1 = 1 - ph(t, 7.7, 8.2);
  if (a1 > 0) {
    g.save(); g.globalAlpha = a1;
    // left: counter + 10 sell ticks
    const c = easeO(ph(t, .05, 1.6));
    ctext('外資', -240, -600, `700 44px ${SANS}`, P.ink);
    ctext('−' + fmt(SELL10 * c), -240, -440, `700 104px ${SERIF}`, GREEN);
    ctext('億', -240, -370, `700 44px ${SANS}`, GREEN);
    DAYS10.forEach((v, i) => { const u = ph(t, .3 + i * .12, .6 + i * .12); if (u <= 0) return; const x = -440 + i * 42, h = -v * .3 * easeO(u); E.inkShape(g, [[x, -300], [x + 30, -300], [x + 30, -300 + h], [x, -300 + h]], { fill: GREEN, hatch: .3, seed: 70 + i, width: 1 }); });
    E.setType(g, '連賣 10 天 ↓', -440, 130, { size: 32, font: SANS, color: GREEN, progress: ph(t, 1.6, 2.2) });
    // divider
    const dv = ph(t, 2.6, 3.0); if (dv > 0) { const p = E.pencilStroke(g, [[0, -640], [0, 170]], { color: P.inkSoft, width: 1.6, progress: dv, seed: 80 }); if (dv < 1) track(p, 0); }
    // right: TAIEX up
    ctext('台股', 240, -600, `700 44px ${SANS}`, P.ink, ph(t, 2.8, 3.1));
    const pts = IDX.map(([d, v], i) => [80 + i * 150, -60 - (v - 38000) * .26]);
    const lu = ph(t, 3.1, 4.4);
    if (lu > 0) { const p = E.pencilStroke(g, pts, { color: RED, width: 6, progress: easeO(lu), seed: 81 }); if (lu < 1) track(p, 1); IDX.forEach(([d], i) => E.setType(g, d, pts[i][0], 40, { size: 22, font: MONO, color: P.inkSoft, align: 'center', progress: ph(lu, i * .4, i * .4 + .3) })); }
    const nu = ph(t, 4.4, 5.4);
    if (nu > 0) { const o = E.handText(g, '+1,112 點', 240, -470, { size: 92, font: HAND, color: RED, progress: nu, align: 'center', weight: 700 }); if (nu < 1) track(o.tip, 1); }
    // the riddle mark
    const qu = ph(t, 6.1, 6.6);
    if (qu > 0) { const o = E.handText(g, '？', 0, 300, { size: 300, font: HAND, color: HI, progress: qu, align: 'center', weight: 700 }); if (qu < 1) track(o.tip, 1); }
    g.restore();
  }

  // ===== Act 2 (8–13): make the number felt =====
  const a2 = ph(t, 8.1, 8.4) * (1 - ph(t, 12.8, 13.2));
  if (a2 > 0) {
    g.save(); g.globalAlpha = a2;
    ctext('外資 11 月搬走', 0, -610, `700 44px ${SANS}`, P.ink);
    ctext(`−${fmt(NOV)} 億`, 0, -500, `700 96px ${SERIF}`, GREEN, ph(t, 8.3, 8.7));
    // crowd of 48 people, coins rising off each
    for (let i = 0; i < 40; i++) {
      const cx = -390 + (i % 8) * 111, cy = -360 + Math.floor(i / 8) * 92, u = ph(t, 8.6 + i * .025, 9.0 + i * .025);
      if (u <= 0) continue;
      g.globalAlpha = a2 * u;
      E.pencilStroke(g, circle(cx, cy - 22, 13, 14), { color: P.ink, width: 2.2, seed: 90 + i });
      E.pencilStroke(g, [[cx - 20, cy + 28], [cx - 16, cy + 2], [cx + 16, cy + 2], [cx + 20, cy + 28]], { color: P.ink, width: 2.2, seed: 140 + i });
      const k = ph(t, 9.6 + (i % 8) * .05, 11.0 + (i % 8) * .05);
      if (k > 0 && k < 1) { g.fillStyle = HI; g.globalAlpha = a2 * (1 - k); g.beginPath(); g.arc(cx + Math.sin(k * 9 + i) * 8, cy - 40 - k * 260, 9, 0, 7); g.fill(); }
    }
    g.globalAlpha = a2;
    const eq = ph(t, 10.7, 11.5);
    if (eq > 0) E.setType(g, `÷ 2,320 萬人`, 0, 110, { size: 40, font: SANS, color: P.inkSoft, align: 'center', progress: eq });
    const pu = ph(t, 10.9, 12.0);
    if (pu > 0) { const o = E.handText(g, `一人 ${(PER / 1e4).toFixed(1)} 萬`, 0, 255, { size: 116, font: HAND, color: HI, progress: pu, align: 'center', weight: 700 }); if (pu < 1) track(o.tip, 1); }
    g.restore();
  }

  // ===== Act 3 (13–23.5): the duel =====
  if (t > 12.9) {
    const a3 = ph(t, 12.9, 13.3);
    g.save(); g.globalAlpha = a3;
    // ledge for the foreign cat
    const lg = ph(t, 13.0, 13.4); if (lg > 0) E.pencilStroke(g, [[-470, -330], [-60, -330]], { color: P.inkSoft, width: 2, progress: lg, seed: 200 });
    track(cat('fii', -270, -500, .95, ph(t, 13.0, 14.6), t), 0);
    E.setType(g, '外資', -270, -650, { size: 40, font: SANS, weight: 900, color: GREY, align: 'center', progress: ph(t, 13.6, 14.0) });
    track(cat('it', 250, -10, 1.0, ph(t, 13.6, 15.2), t), 1);
    E.setType(g, '投信', 250, -150, { size: 40, font: SANS, weight: 900, color: ORANGE, align: 'center', progress: ph(t, 14.2, 14.6) });
    // basket in the orange cat's paws
    const bk = ph(t, 14.8, 15.3); if (bk > 0) E.pencilStroke(g, [[140, 170], [165, 240], [335, 240], [360, 170]], { color: HI, width: 4, progress: bk, seed: 201 });
    // money bags arc from the ledge into the basket (and some miss)
    for (let i = 0; i < 9; i++) {
      const t0 = 15.2 + i * .42, u = (t - t0) / 1.1;
      if (u <= 0 || u > 1.25) continue;
      const miss = i % 3 === 2, x1 = miss ? 470 : 250;
      const x = mix(-150, x1, u), y = -420 + (miss ? 1300 : 880) * u * u - 260 * u;
      if (y > 260 && !miss) continue; if (y > 900) continue;
      bag(x, y, 1.3, '億');
    }
    // the score
    const sL = ph(t, 15.6, 16.6), sR = ph(t, 17.0, 18.0);
    if (sL > 0) { const o = E.handText(g, `2 天 −${Math.round(F2)} 億`, -440, -230, { size: 62, font: HAND, color: GREEN, progress: sL, weight: 700 }); if (sL < 1) track(o.tip, 0); }
    if (sR > 0) { const o = E.handText(g, `2 天 +${Math.round(IT2)} 億`, 110, 120, { size: 62, font: HAND, color: RED, progress: sR, align: 'right', weight: 700 }); if (sR < 1) track(o.tip, 1); }
    // the question: day 11?
    const qd = ph(t, 19.3, 20.3);
    if (qd > 0) { const o = E.handText(g, '第 11 天？', -130, -540, { size: 74, font: HAND, color: HI, progress: qd, align: 'left', weight: 700 }); if (qd < 1) track(o.tip, 1); }
    g.restore();
  }

  if (probe) { probeTip = tip ? { p: tip, f: flip } : null; return; }
  subtitles(t);
  pencil(t, tip, flip, cam);
}

function subtitles(t) {
  const L = LINES.find(l => t >= l.t[0] - .05 && t < l.t[1] + .25);
  if (!L) return;
  const a = cl((t - L.t[0] + .05) / .12) * (1 - cl((t - L.t[1]) / .25));
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = a;
  g.font = `900 58px ${SANS}`; g.textAlign = 'center'; g.lineJoin = 'round';
  const lh = 76, n = L.txt.length, bottom = 1500;
  L.txt.forEach((s, i) => { const y = bottom - (n - 1 - i) * lh; g.strokeStyle = 'rgba(10,11,14,.92)'; g.lineWidth = 12; g.strokeText(s, 500, y); g.fillStyle = '#FFF'; g.fillText(s, 500, y); });
  g.restore();
}

const TIPS = [];
function pencil(t, tip, flip, cam) {
  const fi = Math.round(t * 24);
  let lift = 0, pos = tip, fl = flip;
  if (!pos) {
    let a = null, b = null;
    for (let k = fi; k >= 0; k--) if (TIPS[k]) { a = { k, ...TIPS[k] }; break; }
    for (let k = fi; k < TIPS.length; k++) if (TIPS[k]) { b = { k, ...TIPS[k] }; break; }
    if (!a && !b) return;
    if (a && b && b.k - a.k < 60) { const u = (fi - a.k) / Math.max(1, b.k - a.k); pos = [mix(a.p[0], b.p[0], u), mix(a.p[1], b.p[1], u)]; lift = Math.sin(u * Math.PI) * .9 + .15; fl = u < .5 ? a.f : b.f; }
    else if (b && (!a || fi - a.k > b.k - fi)) { const u = cl((b.k - fi) / 16); if (u >= 1) return; pos = [b.p[0] + 500 * u, b.p[1] + 700 * u]; lift = .15 + u; fl = b.f; }
    else { const u = cl((fi - a.k) / 16); if (u >= 1) return; pos = [a.p[0] + 500 * easeO(u), a.p[1] + 700 * easeO(u)]; lift = .15 + u; fl = a.f; }
  }
  E.drawPencil(g, { tip: E.w2s(cam, pos[0], pos[1]), s: .5, lift, flip: fl });
}
for (let f = 0; f <= DUR * 24; f++) { probe = true; render(f / 24); probe = false; TIPS.push(probeTip); }
window.DUR = DUR;
window.render = t => render(t);
window.READY = true;
