/**
 * Firma visual del aplicativo: el TEJIDO EMPRESARIAL.
 * Decenas de empresas (nodos) se entrelazan con hilos que convergen en un
 * núcleo —la base empresarial— y se proyectan hacia los tres ejes de negocio
 * de ProColombia: Exportaciones, Inversión y Turismo. Los impulsos que
 * recorren los hilos representan información fluyendo hacia cada eje.
 *
 * Decorativo (aria-hidden). Geometría determinista (mismo render siempre).
 * Todo el movimiento vive en CSS y respeta prefers-reduced-motion.
 */

const NUCLEO = { x: 810, y: 300 };

/* Los ejes del lado derecho se limitan para que sus etiquetas nunca superen
   x ≈ 1150 del viewBox (1200): así son visibles con cualquier ancho de pantalla. */
export const EJES = [
  { id: 'expo', nombre: 'Exportaciones', color: '#ffa400', angulo: -64, radio: 210 },
  { id: 'inv', nombre: 'Inversión', color: '#4fc3f7', angulo: 14, radio: 205 },
  { id: 'tur', nombre: 'Turismo', color: '#7ed957', angulo: 98, radio: 200 },
] as const;

function polar(cx: number, cy: number, grados: number, radio: number) {
  const rad = (grados * Math.PI) / 180;
  return { x: cx + radio * Math.cos(rad), y: cy + radio * Math.sin(rad) };
}

const HUBS = EJES.map((eje) => ({ ...eje, ...polar(NUCLEO.x, NUCLEO.y, eje.angulo, eje.radio) }));

/** Empresas: 42 nodos distribuidos en anillos con desfase determinista. */
const EMPRESAS = Array.from({ length: 42 }, (_, i) => {
  const anillo = i % 3;
  const radio = 90 + anillo * 62 + ((i * 37) % 28);
  const angulo = (i * 360) / 42 + (i % 2 ? 9 : -6) + anillo * 5;
  const { x, y } = polar(NUCLEO.x, NUCLEO.y, angulo, radio);
  const hub = HUBS[(i + anillo) % HUBS.length];
  return { x, y, r: 2 + (i % 3) * 0.9, hub, clase: i % 4 };
});

/** Hilos de la trama (fondo): líneas suaves que sugieren un tejido. */
const TRAMA = Array.from({ length: 7 }, (_, i) => 60 + i * 78);

const PARTICULAS = Array.from({ length: 18 }, (_, i) => ({
  x: 420 + ((i * 131) % 720),
  y: 60 + ((i * 197) % 480),
  r: 1.1 + (i % 3) * 0.6,
  retraso: (i * 0.8) % 9,
}));

export function TejidoPortada() {
  return (
    <svg className="portada__fondo" viewBox="0 0 1200 600" preserveAspectRatio="xMaxYMid slice" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="tp-fondo" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#011627" />
          <stop offset="0.55" stopColor="#062b43" />
          <stop offset="1" stopColor="#0c4468" />
        </linearGradient>
        <radialGradient id="tp-halo" cx="0.72" cy="0.5" r="0.55">
          <stop offset="0" stopColor="#ffa400" stopOpacity="0.22" />
          <stop offset="0.6" stopColor="#ffa400" stopOpacity="0.06" />
          <stop offset="1" stopColor="#ffa400" stopOpacity="0" />
        </radialGradient>
        <radialGradient id="tp-nucleo" cx="0.5" cy="0.5" r="0.5">
          <stop offset="0" stopColor="#ffc35c" stopOpacity="0.55" />
          <stop offset="0.5" stopColor="#ffa400" stopOpacity="0.18" />
          <stop offset="1" stopColor="#ffa400" stopOpacity="0" />
        </radialGradient>
        <pattern id="tp-reticula" width="46" height="46" patternUnits="userSpaceOnUse">
          <path d="M46 0H0v46" fill="none" stroke="rgba(255,255,255,0.045)" strokeWidth="1" />
        </pattern>
        {HUBS.map((hub) => (
          <radialGradient key={hub.id} id={`tp-glow-${hub.id}`} cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={hub.color} stopOpacity="0.5" />
            <stop offset="1" stopColor={hub.color} stopOpacity="0" />
          </radialGradient>
        ))}
      </defs>

      <rect width="1200" height="600" fill="url(#tp-fondo)" />
      <rect width="1200" height="600" fill="url(#tp-reticula)" />
      <rect width="1200" height="600" fill="url(#tp-halo)" />

      {/* trama de fondo: hilos horizontales ondulados en deriva lenta */}
      <g className="tejido__trama" fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="1">
        {TRAMA.map((y, i) => (
          <path
            key={y}
            d={`M -60 ${y} C 140 ${y - 18 + (i % 2) * 36}, 320 ${y + 18 - (i % 2) * 36}, 520 ${y} S 900 ${y + (i % 2 ? -14 : 14)}, 1300 ${y}`}
          />
        ))}
      </g>

      {/* órbitas de contexto */}
      <circle cx={NUCLEO.x} cy={NUCLEO.y} r={150} fill="none" stroke="rgba(255,255,255,0.05)" />
      <circle cx={NUCLEO.x} cy={NUCLEO.y} r={215} fill="none" stroke="rgba(255,255,255,0.035)" strokeDasharray="3 9" />

      {/* partículas ambientales */}
      <g fill="#ffc35c">
        {PARTICULAS.map((p, i) => (
          <circle key={i} className="tejido__particula" cx={p.x} cy={p.y} r={p.r} style={{ animationDelay: `${p.retraso}s` }} />
        ))}
      </g>

      {/* hilos empresa → eje: cada empresa aporta información a un eje */}
      <g fill="none" strokeWidth="0.9">
        {EMPRESAS.map((e, i) => {
          const mx = (e.x + e.hub.x) / 2 + (i % 2 ? 14 : -14);
          const my = (e.y + e.hub.y) / 2 + (i % 3 === 0 ? -12 : 10);
          const d = `M ${e.x.toFixed(1)} ${e.y.toFixed(1)} Q ${mx.toFixed(1)} ${my.toFixed(1)} ${e.hub.x.toFixed(1)} ${e.hub.y.toFixed(1)}`;
          return (
            <g key={i}>
              <path d={d} stroke="rgba(255,255,255,0.10)" />
              {i % 3 === 0 && (
                <path
                  className="tejido__impulso"
                  d={d}
                  pathLength={260}
                  stroke={e.hub.color}
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeDasharray="14 246"
                  style={{ animationDelay: `${(i * 0.37) % 4.8}s` }}
                />
              )}
            </g>
          );
        })}
      </g>

      {/* hilos núcleo → ejes (gruesos) */}
      <g fill="none" strokeWidth="2">
        {HUBS.map((hub, i) => {
          const mx = (NUCLEO.x + hub.x) / 2 + (i % 2 ? 18 : -18);
          const my = (NUCLEO.y + hub.y) / 2 + (i % 2 ? -12 : 12);
          const d = `M ${NUCLEO.x} ${NUCLEO.y} Q ${mx.toFixed(1)} ${my.toFixed(1)} ${hub.x.toFixed(1)} ${hub.y.toFixed(1)}`;
          return (
            <g key={hub.id}>
              <path d={d} stroke="rgba(255,255,255,0.28)" />
              <path className="tejido__impulso" d={d} pathLength={260} stroke={hub.color} strokeWidth="3" strokeLinecap="round" strokeDasharray="22 238" style={{ animationDelay: `${i * 1.6}s` }} />
            </g>
          );
        })}
      </g>

      {/* empresas */}
      <g>
        {EMPRESAS.map((e, i) => (
          <circle key={i} className={`tejido__nodo tejido__nodo--${e.clase % 3}`} cx={e.x.toFixed(1)} cy={e.y.toFixed(1)} r={e.r} fill={i % 5 === 0 ? e.hub.color : 'rgba(255,255,255,0.75)'} opacity={0.8} />
        ))}
      </g>

      {/* ondas del núcleo */}
      <circle className="tejido__onda" cx={NUCLEO.x} cy={NUCLEO.y} r={40} fill="none" stroke="rgba(255,195,92,0.6)" strokeWidth="1.2" />
      <circle className="tejido__onda tejido__onda--2" cx={NUCLEO.x} cy={NUCLEO.y} r={40} fill="none" stroke="rgba(255,195,92,0.6)" strokeWidth="1.2" />
      <circle className="tejido__onda tejido__onda--3" cx={NUCLEO.x} cy={NUCLEO.y} r={40} fill="none" stroke="rgba(255,195,92,0.6)" strokeWidth="1.2" />

      {/* núcleo: la base empresarial */}
      <circle cx={NUCLEO.x} cy={NUCLEO.y} r={92} fill="url(#tp-nucleo)" />
      <circle className="tejido__nucleo" cx={NUCLEO.x} cy={NUCLEO.y} r={22} fill="#ffa400" />
      <circle cx={NUCLEO.x} cy={NUCLEO.y} r={30} fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth="1.5" />
      <circle cx={NUCLEO.x} cy={NUCLEO.y} r={9} fill="#011627" />

      {/* ejes */}
      {HUBS.map((hub, i) => (
        <g key={hub.id}>
          <circle cx={hub.x} cy={hub.y} r={56} fill={`url(#tp-glow-${hub.id})`} />
          <circle className={`tejido__eje-halo tejido__eje-halo--${i}`} cx={hub.x} cy={hub.y} r={26} fill="none" stroke={hub.color} strokeWidth="1.2" />
          <circle cx={hub.x} cy={hub.y} r={15} fill="#011627" stroke={hub.color} strokeWidth="2.5" />
          <circle cx={hub.x} cy={hub.y} r={6} fill={hub.color} />
        </g>
      ))}

      {/* etiquetas de los ejes */}
      <g className="tejido__etiquetas" fontFamily="'IBM Plex Mono', ui-monospace, monospace" fontSize="12" letterSpacing="1.4" fill="#e8eef3">
        {HUBS.map((hub) => {
          const derecha = hub.x >= NUCLEO.x;
          const x = hub.x + (derecha ? 34 : -34);
          return (
            <g key={hub.id}>
              <text x={x} y={hub.y - 4} textAnchor={derecha ? 'start' : 'end'} fontWeight="600">
                {hub.nombre.toUpperCase()}
              </text>
              <text x={x} y={hub.y + 13} textAnchor={derecha ? 'start' : 'end'} fontSize="10" fill="#9db1bf" letterSpacing="1">
                EJE DE NEGOCIO
              </text>
            </g>
          );
        })}
        <text x={NUCLEO.x} y={NUCLEO.y + 58} textAnchor="middle" fontWeight="600" fill="#ffc35c">
          TEJIDO EMPRESARIAL
        </text>
        <text x={NUCLEO.x} y={NUCLEO.y + 74} textAnchor="middle" fontSize="10" fill="#9db1bf" letterSpacing="1">
          BASE DE EMPRESAS DE COLOMBIA
        </text>
      </g>
    </svg>
  );
}
