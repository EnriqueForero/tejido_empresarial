import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { obtenerMetadatos } from '../api';
import { ContadorAnimado, Revelar } from '../componentes/Interfaz';
import { EJES, TejidoPortada } from '../componentes/TejidoPortada';
import type { Metadatos } from '../tipos';

/* Contenido institucional del aplicativo original (Descripción, Beneficios, Alcance y límites). */
const PESTANAS = [
  {
    id: 'descripcion',
    titulo: 'Descripción general',
    contenido: (
      <p>
        Esta herramienta brinda acceso a información clave sobre el tejido empresarial colombiano, con un enfoque en productos y
        servicios no minero-energéticos. Está diseñada para apoyar la gestión comercial de los asesores de ProColombia, proporcionando
        una fuente ágil y eficiente que facilita y optimiza los procesos de identificación, segmentación y priorización de empresas,
        contribuyendo a una atención estratégica más efectiva en los ejes de Exportaciones, Inversión y Turismo.
      </p>
    ),
  },
  {
    id: 'beneficios',
    titulo: 'Beneficios',
    contenido: (
      <ul>
        <li>Segmentar empresas por múltiples criterios alineados con la estrategia, facilitando el cumplimiento de métricas.</li>
        <li>Facilitar la identificación y priorización de empresas según las características que el asesor requiera.</li>
        <li>Detectar nuevas empresas para brindarles los servicios ofrecidos por ProColombia.</li>
        <li>Identificar empresas objetivo para invitarlas a eventos específicos.</li>
        <li>
          Obtener un perfil de cada empresa con actividad económica, información financiera, historial exportador y datos de
          contacto.
        </li>
        <li>
          Centralizar la información de distintas bases empresariales en un solo lugar, reduciendo el tiempo y esfuerzo de búsqueda.
        </li>
      </ul>
    ),
  },
  {
    id: 'alcance',
    titulo: 'Alcance y límites',
    contenido: (
      <ul>
        <li>Abarca tanto empresas de bienes como de servicios.</li>
        <li>
          Información netamente cuantitativa que facilita la identificación y el filtrado. La segmentación final debe ser realizada por
          los asesores según sus propios criterios y aspectos cualitativos.
        </li>
        <li>No reemplaza otras bases de datos o herramientas desarrolladas por la Gerencia de Inteligencia Comercial.</li>
        <li>No sustituye los análisis de la Vicepresidencia de Planeación; los complementa para una mejor toma de decisiones.</li>
        <li>
          Las cifras de exportación de servicios provienen de los negocios reportados a ProColombia y no representan el total de la
          exportación de estos sectores en el país.
        </li>
      </ul>
    ),
  },
];

const TARJETAS_EJES = [
  {
    eje: EJES[0],
    codigo: 'EJE 01',
    texto: 'Encuentre exportadoras y futuras exportadoras por cadena, trayectoria, sector, posición arancelaria y mercado de destino.',
    puntos: ['Trayectoria exportadora y valor FOB por año', 'Cadena, sector y subsector estrella', 'HUB y país de destino'],
    icono: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M3 14h14M4 14l4-6 3 3 5-6" />
      </svg>
    ),
  },
  {
    eje: EJES[1],
    codigo: 'EJE 02',
    texto: 'Comprenda ubicación, tamaño, antigüedad, finanzas, empleo y señales de capital extranjero en cada territorio.',
    puntos: ['Ingresos, activos, utilidad y empleados', 'Inversión extranjera y macrorregión', 'Actividad económica CIIU'],
    icono: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 17V8l6-4 6 4v9M8 17v-5h4v5" />
      </svg>
    ),
  },
  {
    eje: EJES[2],
    codigo: 'EJE 03',
    texto: 'Identifique el tejido empresarial de la cadena de turismo y construya lecturas territoriales más informadas.',
    puntos: ['Cadena de segmentación Turismo', 'Alojamiento, agencias y servicios conexos', 'Departamento y municipio de la sede'],
    icono: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M10 17s-5-4.4-5-8a5 5 0 0 1 10 0c0 3.6-5 8-5 8z" />
        <circle cx="10" cy="9" r="1.8" />
      </svg>
    ),
  },
];

function usarParalaje() {
  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    const seccion = ref.current;
    if (!seccion || typeof window.matchMedia !== 'function') return;
    const puedeMoverse = window.matchMedia('(pointer: fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!puedeMoverse) return;
    let marco = 0;
    const alMover = (evento: PointerEvent) => {
      cancelAnimationFrame(marco);
      marco = requestAnimationFrame(() => {
        const caja = seccion.getBoundingClientRect();
        seccion.style.setProperty('--px', (((evento.clientX - caja.left) / caja.width - 0.5) * 2).toFixed(3));
        seccion.style.setProperty('--py', (((evento.clientY - caja.top) / caja.height - 0.5) * 2).toFixed(3));
      });
    };
    const alSalir = () => {
      cancelAnimationFrame(marco);
      seccion.style.setProperty('--px', '0');
      seccion.style.setProperty('--py', '0');
    };
    seccion.addEventListener('pointermove', alMover);
    seccion.addEventListener('pointerleave', alSalir);
    return () => {
      seccion.removeEventListener('pointermove', alMover);
      seccion.removeEventListener('pointerleave', alSalir);
      cancelAnimationFrame(marco);
    };
  }, []);
  return ref;
}

export default function Inicio() {
  const portadaRef = usarParalaje();
  const [pestana, setPestana] = useState(PESTANAS[0].id);
  const [meta, setMeta] = useState<Metadatos | null>(null);
  useEffect(() => {
    obtenerMetadatos().then(setMeta).catch(() => setMeta(null));
  }, []);
  const variables = meta?.export_columns.length ?? 63;
  const filtros = meta?.filters.length ?? 19;
  const activa = PESTANAS.find((p) => p.id === pestana) ?? PESTANAS[0];

  return (
    <div className="pagina pagina--portada">
      <section ref={portadaRef} className="portada" aria-label="Presentación del aplicativo">
        <TejidoPortada />
        <div className="portada__interior">
          <div className="portada__contenido">
            <p className="portada__kicker">ProColombia · Gerencia de Inteligencia Comercial</p>
            <h1 className="portada__titulo">
              El tejido empresarial de Colombia, <em>al servicio de cada oportunidad.</em>
            </h1>
            <p className="portada__bajada">
              Identifique, segmente y comprenda empresas colombianas con información integrada de RUES, Supersociedades, DANE–DIAN y
              el CRM de ProColombia. Una sola base para los tres ejes de negocio: Exportaciones, Inversión y Turismo.
            </p>
            <div className="portada__acciones">
              <Link className="boton boton--cinta boton--xl" to="/consultar">
                Consultar empresas <span className="boton__flecha" aria-hidden="true">→</span>
              </Link>
              <Link className="boton boton--vidrio boton--xl" to="/glosario">
                Conocer las variables
              </Link>
            </div>
            <div className="portada__ejes" aria-label="Ejes de negocio de ProColombia">
              {EJES.map((eje) => (
                <span key={eje.id} className="portada__eje" style={{ '--eje': eje.color } as React.CSSProperties}>
                  <i aria-hidden="true" />
                  {eje.nombre}
                </span>
              ))}
            </div>
            <dl className="portada__cifras">
              <div>
                <dt className="dato">
                  <ContadorAnimado valor={String(variables)} />
                </dt>
                <dd>variables por empresa en la descarga</dd>
              </div>
              <div>
                <dt className="dato">
                  <ContadorAnimado valor={String(filtros)} />
                </dt>
                <dd>filtros combinables y dependientes</dd>
              </div>
              <div>
                <dt className="dato">
                  <ContadorAnimado valor="4" />
                </dt>
                <dd>fuentes oficiales integradas</dd>
              </div>
              <div>
                <dt className="dato">
                  <ContadorAnimado valor="3" />
                </dt>
                <dd>ejes de negocio atendidos</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="mt-40" aria-labelledby="t-ejes">
        <Revelar>
          <div className="encabezado-seccion">
            <div>
              <p className="kicker">Una base, tres ejes</p>
              <h2 id="t-ejes">
                <span className="marcador-nucleo" aria-hidden="true" />
                Información empresarial para Exportaciones, Inversión y Turismo
              </h2>
              <span className="cinta" aria-hidden="true" />
            </div>
            <p className="texto-suave chico">Empresas de bienes y servicios · foco en productos no minero-energéticos</p>
          </div>
        </Revelar>
        <div className="ejes-grid mt-20">
          {TARJETAS_EJES.map((tarjeta, i) => (
            <Revelar key={tarjeta.eje.id} retraso={i * 80}>
              <article className="tarjeta tarjeta--interactiva eje-tarjeta" style={{ '--eje': tarjeta.eje.color } as React.CSSProperties}>
                <div className="eje-tarjeta__cab">
                  <span className="eje-tarjeta__codigo">{tarjeta.codigo}</span>
                  <span className="eje-tarjeta__icono">{tarjeta.icono}</span>
                </div>
                <h3>{tarjeta.eje.nombre}</h3>
                <p>{tarjeta.texto}</p>
                <ul>
                  {tarjeta.puntos.map((punto) => (
                    <li key={punto}>{punto}</li>
                  ))}
                </ul>
                <Link to="/consultar" className="eje-tarjeta__enlace">
                  Consultar empresas →
                </Link>
              </article>
            </Revelar>
          ))}
        </div>
      </section>

      <section className="salto-superior" aria-labelledby="t-acerca">
        <Revelar>
          <p className="kicker">Acerca de la herramienta</p>
          <h2 id="t-acerca">
            <span className="marcador-nucleo" aria-hidden="true" />
            Qué es, para qué sirve y hasta dónde llega
          </h2>
          <span className="cinta" aria-hidden="true" />
          <div className="pestanas mt-20" role="tablist" aria-label="Secciones descriptivas">
            {PESTANAS.map((p) => (
              <button
                key={p.id}
                role="tab"
                id={`tab-${p.id}`}
                type="button"
                aria-selected={pestana === p.id}
                aria-controls={`panel-${p.id}`}
                tabIndex={pestana === p.id ? 0 : -1}
                onClick={() => setPestana(p.id)}
                onKeyDown={(evento) => {
                  const indice = PESTANAS.findIndex((x) => x.id === pestana);
                  if (evento.key === 'ArrowRight') setPestana(PESTANAS[(indice + 1) % PESTANAS.length].id);
                  if (evento.key === 'ArrowLeft') setPestana(PESTANAS[(indice - 1 + PESTANAS.length) % PESTANAS.length].id);
                }}
              >
                {p.titulo}
              </button>
            ))}
          </div>
          <div className="tarjeta panel-pestana" role="tabpanel" id={`panel-${activa.id}`} aria-labelledby={`tab-${activa.id}`}>
            {activa.contenido}
          </div>
        </Revelar>
      </section>

      <section className="salto-superior" aria-labelledby="t-pasos">
        <Revelar>
          <div className="encabezado-seccion">
            <div>
              <p className="kicker">Cómo se usa</p>
              <h2 id="t-pasos">
                <span className="marcador-nucleo" aria-hidden="true" />
                De la pregunta al archivo, en tres pasos
              </h2>
              <span className="cinta" aria-hidden="true" />
            </div>
            <Link to="/consultar" className="boton boton--fantasma boton--chico">
              Ir a consultar <span className="boton__flecha" aria-hidden="true">→</span>
            </Link>
          </div>
        </Revelar>
        <ol className="pasos mt-20">
          {[
            ['Busque', 'Combine filtros dependientes por ubicación, perfil, actividad y exportaciones; o busque por razón social, NIT o un lote de NIT desde un archivo .txt.'],
            ['Revise', 'Vea primero las variables esenciales, ordene la tabla, elija columnas y abra la ficha completa de cualquier empresa.'],
            ['Descargue', 'Obtenga un Excel listo para leer: resumen de la consulta, vista principal, datos completos y diccionario de variables.'],
          ].map(([titulo, texto], i) => (
            <Revelar key={titulo} retraso={i * 80}>
              <li className="tarjeta paso">
                <span className="paso__num" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span>
                  <strong>{titulo}</strong>
                  <p>{texto}</p>
                </span>
              </li>
            </Revelar>
          ))}
        </ol>
      </section>

      <section className="salto-superior" aria-labelledby="t-fuentes">
        <Revelar>
          <div className="encabezado-seccion">
            <div>
              <p className="kicker">Transparencia desde el origen</p>
              <h2 id="t-fuentes">
                <span className="marcador-nucleo" aria-hidden="true" />
                Cada variable conserva su definición, su fuente y su corte
              </h2>
              <span className="cinta" aria-hidden="true" />
            </div>
            <Link to="/metodologia" className="boton boton--fantasma boton--chico">
              Ver metodología <span className="boton__flecha" aria-hidden="true">→</span>
            </Link>
          </div>
        </Revelar>
        <div className="fuentes-grid mt-20">
          {(meta?.sources ?? [
            { name: 'RUES', detail: 'Registro Único Empresarial y Social', cut: 'corte 30 de junio de 2026' },
            { name: 'Supersociedades', detail: 'Las 10.000 empresas más grandes de Colombia', cut: '2025' },
            { name: 'DANE – DIAN', detail: 'Exportaciones de bienes', cut: '2021 - Enero a Mayo 2026' },
            { name: 'CRM ProColombia', detail: 'Negocios de Industrias 4.0 y relación institucional', cut: '2021 - Enero a Mayo 2026' },
          ]).map((fuente, i) => (
            <Revelar key={fuente.name} retraso={i * 60}>
              <div className="tarjeta tarjeta--interactiva fuente">
                <strong>{fuente.name}</strong>
                <span>{fuente.detail}</span>
                <b>{fuente.cut}</b>
              </div>
            </Revelar>
          ))}
        </div>
        <Revelar>
          <div className="franja-cta">
            <div>
              <p className="kicker kicker--claro">Listo para consultar</p>
              <h2>Encuentre hoy las empresas que su estrategia necesita.</h2>
              <p>Resultados legibles en pantalla, ficha por empresa y una descarga Excel con formato profesional y diccionario incluido.</p>
            </div>
            <div className="acciones">
              <Link className="boton boton--cinta boton--xl" to="/consultar">
                Consultar empresas <span className="boton__flecha" aria-hidden="true">→</span>
              </Link>
              <Link className="boton boton--vidrio boton--xl" to="/glosario">
                Glosario de variables
              </Link>
            </div>
          </div>
        </Revelar>
      </section>
    </div>
  );
}
