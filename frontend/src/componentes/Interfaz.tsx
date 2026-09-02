/**
 * Componentes de interfaz transversales: revelado al hacer scroll, contador
 * animado, cabecera de página, avisos, spinner, botón «volver arriba»,
 * pastilla de estado y ayuda contextual. Todo movimiento respeta
 * prefers-reduced-motion.
 */
import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { prefiereMenosMovimiento, useCerrarAlExterior, useVisible } from '../hooks';

export function Revelar({ children, className = '', retraso = 0 }: { children: ReactNode; className?: string; retraso?: number }) {
  const { ref, visible } = useVisible<HTMLDivElement>();
  return (
    <div
      ref={ref}
      className={`revelar ${visible ? 'es-visible' : ''} ${className}`.trim()}
      style={retraso ? ({ '--retraso': `${retraso}ms` } as React.CSSProperties) : undefined}
    >
      {children}
    </div>
  );
}

/** Cuenta desde 0 hasta el valor cuando entra en pantalla. Soporta sufijos («61», «4 fuentes»). */
export function ContadorAnimado({ valor, duracion = 1100 }: { valor: string; duracion?: number }) {
  const { ref, visible } = useVisible<HTMLSpanElement>();
  const [texto, setTexto] = useState<string>(() => {
    const m = valor.match(/^(\d+(?:[.,]\d+)?)([\s\S]*)$/);
    return m ? `0${m[2]}` : valor;
  });
  useEffect(() => {
    if (!visible) return;
    const m = valor.match(/^(\d+(?:[.,]\d+)?)([\s\S]*)$/);
    if (!m || prefiereMenosMovimiento()) {
      setTexto(valor);
      return;
    }
    const usaComa = m[1].includes(',');
    const objetivo = parseFloat(m[1].replace(',', '.'));
    const decimales = /[.,]/.test(m[1]) ? m[1].split(/[.,]/)[1].length : 0;
    const sufijo = m[2];
    let inicio: number | null = null;
    let cuadro = 0;
    const paso = (t: number) => {
      if (inicio === null) inicio = t;
      const avance = Math.min((t - inicio) / duracion, 1);
      const suavizado = 1 - Math.pow(1 - avance, 3);
      const actual = (objetivo * suavizado).toFixed(decimales);
      setTexto(`${usaComa ? actual.replace('.', ',') : actual}${sufijo}`);
      if (avance < 1) cuadro = requestAnimationFrame(paso);
      else setTexto(valor);
    };
    cuadro = requestAnimationFrame(paso);
    const seguro = window.setTimeout(() => setTexto(valor), duracion + 600);
    return () => {
      cancelAnimationFrame(cuadro);
      window.clearTimeout(seguro);
    };
  }, [visible, valor, duracion]);
  return <span ref={ref}>{texto}</span>;
}

export function CabeceraPagina({
  kicker,
  titulo,
  tituloId,
  bajada,
  lateral,
  oscura = false,
}: {
  kicker: string;
  titulo: ReactNode;
  tituloId?: string;
  bajada?: ReactNode;
  lateral?: ReactNode;
  oscura?: boolean;
}) {
  return (
    <header className={`cabecera-pagina ${oscura ? 'cabecera-pagina--oscura' : ''}`}>
      <div className="cabecera-pagina__interior">
        <div className="cabecera-pagina__fila">
          <div>
            <p className="kicker">{kicker}</p>
            <h1 id={tituloId}>{titulo}</h1>
            <span className="cinta" aria-hidden="true" />
            {bajada && <div className="cabecera-pagina__bajada">{bajada}</div>}
          </div>
          {lateral && <div className="cabecera-pagina__lateral">{lateral}</div>}
        </div>
      </div>
    </header>
  );
}

export function Aviso({ tipo = 'info', children, rol }: { tipo?: 'info' | 'advertencia' | 'error' | 'ok'; children: ReactNode; rol?: 'alert' | 'status' }) {
  return (
    <div className={`aviso aviso--${tipo}`} role={rol ?? (tipo === 'error' ? 'alert' : 'status')}>
      {children}
    </div>
  );
}

export function Spinner({ oscuro = false }: { oscuro?: boolean }) {
  return <span className={`spinner ${oscuro ? 'spinner--oscuro' : ''}`} aria-hidden="true" />;
}

export function Pastilla({ children, tono = 'neutro' }: { children: ReactNode; tono?: 'neutro' | 'acento' | 'ok' | 'alerta' | 'azul' }) {
  return <span className={`etiqueta-mini etiqueta-mini--${tono}`}>{children}</span>;
}

/** Botón «?» con globo de ayuda accesible (clic o foco). */
export function Ayuda({ texto, etiqueta }: { texto: string; etiqueta: string }) {
  const [abierto, setAbierto] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);
  const id = useId();
  useCerrarAlExterior(abierto, ref, () => setAbierto(false));
  return (
    <span className="ayuda" ref={ref}>
      <button
        type="button"
        className="ayuda__boton"
        aria-label={`Ayuda sobre ${etiqueta}`}
        aria-expanded={abierto}
        aria-controls={id}
        onClick={(evento) => {
          evento.stopPropagation();
          setAbierto((valor) => !valor);
        }}
      >
        ?
      </button>
      <span id={id} role="tooltip" className={`ayuda__globo ${abierto ? 'ayuda__globo--visible' : ''}`}>
        {texto}
      </span>
    </span>
  );
}

export function BotonArriba() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    let marco = 0;
    const alDesplazar = () => {
      cancelAnimationFrame(marco);
      marco = requestAnimationFrame(() => setVisible(window.scrollY > 640));
    };
    alDesplazar();
    window.addEventListener('scroll', alDesplazar, { passive: true });
    return () => {
      window.removeEventListener('scroll', alDesplazar);
      cancelAnimationFrame(marco);
    };
  }, []);
  return (
    <button
      type="button"
      className={`boton-arriba ${visible ? 'boton-arriba--visible' : ''}`}
      aria-label="Volver al inicio de la página"
      onClick={() => window.scrollTo({ top: 0, behavior: prefiereMenosMovimiento() ? 'auto' : 'smooth' })}
    >
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true" focusable="false">
        <path d="M9 14V4M4.5 8.5 9 4l4.5 4.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </button>
  );
}

export function EstadoVacio({ titulo, texto, icono = '0', children }: { titulo: string; texto?: ReactNode; icono?: string; children?: ReactNode }) {
  return (
    <div className="estado-vacio" role="status">
      <span className="estado-vacio__icono dato" aria-hidden="true">
        {icono}
      </span>
      <h3>{titulo}</h3>
      {texto && <p>{texto}</p>}
      {children}
    </div>
  );
}

/** Icono lineal para tipos de archivo. */
export function IconoArchivo({ tipo }: { tipo: 'XLSX' | 'DOCX' | 'TXT' }) {
  const trazo =
    tipo === 'XLSX' ? (
      <path d="M4 1.5h5.5L13 5v9.5H4zM9.5 1.5V5H13M6 8.5l4 4M10 8.5l-4 4" />
    ) : tipo === 'DOCX' ? (
      <path d="M4 1.5h5.5L13 5v9.5H4zM9.5 1.5V5H13M6 8l1.2 3.5L8.5 8l1.3 3.5L11 8" />
    ) : (
      <path d="M4 1.5h5.5L13 5v9.5H4zM9.5 1.5V5H13M6 8h5M6 10.5h5M6 13h3" />
    );
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round">
      {trazo}
    </svg>
  );
}
