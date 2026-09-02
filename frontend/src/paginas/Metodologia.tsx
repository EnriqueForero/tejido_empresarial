import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { obtenerGlosario, obtenerMetadatos } from '../api';
import { CabeceraPagina, IconoArchivo, Revelar } from '../componentes/Interfaz';
import type { EntradaGlosario, Metadatos } from '../tipos';

const CLAVES = ['Trayectoria exportadora', 'Cadena de segmentación', 'Valor Agregado - Actividad principal', 'Empresa exportadora NME según actividad económica', 'Tamaño de la empresa', 'Inversión extranjera'];

function Definicion({ entrada }: { entrada: EntradaGlosario }) {
  const parrafos = entrada.description_paragraphs.length ? entrada.description_paragraphs : [entrada.description];
  const [intro, ...resto] = parrafos;
  return (
    <article className="tarjeta definicion">
      <h3>{entrada.variable}</h3>
      <p>{intro}</p>
      {resto.length > 0 && (
        <ul>
          {resto.slice(0, 6).map((linea, i) => (
            <li key={i}>{linea}</li>
          ))}
          {resto.length > 6 && (
            <li>
              <Link to={`/glosario?v=${encodeURIComponent(entrada.variable)}`}>Ver la definición completa en el glosario →</Link>
            </li>
          )}
        </ul>
      )}
      <p className="texto-suave chico mt-8">Fuente: {entrada.sources}</p>
    </article>
  );
}

export default function Metodologia() {
  const [meta, setMeta] = useState<Metadatos | null>(null);
  const [claves, setClaves] = useState<EntradaGlosario[]>([]);
  useEffect(() => {
    obtenerMetadatos().then(setMeta).catch(() => setMeta(null));
    obtenerGlosario()
      .then((glosario) => setClaves(CLAVES.map((nombre) => glosario.entries.find((e) => e.variable === nombre)).filter((e): e is EntradaGlosario => Boolean(e))))
      .catch(() => setClaves([]));
  }, []);

  return (
    <>
      <CabeceraPagina
        oscura
        kicker="Metodología, fuentes y alcance"
        titulo="Datos claros, decisiones con criterio."
        bajada="Qué cubre el aplicativo, de dónde provienen sus variables, con qué cortes y cómo interpretarlas antes de convertirlas en una decisión comercial."
        lateral={
          <>
            <a className="boton boton--cinta" href="/api/resources/methodology.docx" download>
              <IconoArchivo tipo="DOCX" /> Metodología completa
            </a>
            <a className="boton boton--vidrio" href="/api/resources/glossary.xlsx" download>
              <IconoArchivo tipo="XLSX" /> Glosario (Excel)
            </a>
          </>
        }
      />
      <div className="pagina metodologia">
        <section aria-labelledby="t-proposito">
          <Revelar>
            <p className="kicker">01 · Propósito</p>
            <h2 id="t-proposito">Una base cuantitativa para identificar, segmentar y priorizar</h2>
            <span className="cinta" aria-hidden="true" />
            <p>
              El aplicativo centraliza información del tejido empresarial colombiano —empresas de bienes y servicios, con foco en productos no minero-energéticos— para apoyar la gestión comercial de los equipos de ProColombia en
              los ejes de Exportaciones, Inversión y Turismo. Integra registro mercantil, estados financieros, exportaciones de bienes y la relación con ProColombia en un perfil único por empresa.
            </p>
          </Revelar>
          <div className="grid grid--3 mt-20">
            {[
              ['Identificar', 'Encontrar empresas con características relevantes para un objetivo concreto: territorio, tamaño, actividad, mercados.'],
              ['Segmentar', 'Combinar criterios que se cruzan entre sí y cuyas opciones se ajustan a lo ya seleccionado.'],
              ['Priorizar', 'Ordenar por ingresos, revisar la trayectoria exportadora y llevar el segmento a Excel para el trabajo posterior.'],
            ].map(([titulo, texto], i) => (
              <Revelar key={titulo} retraso={i * 70}>
                <article className="tarjeta tarjeta--interactiva">
                  <h3>{titulo}</h3>
                  <p className="texto-suave mt-8">{texto}</p>
                </article>
              </Revelar>
            ))}
          </div>
        </section>

        <section aria-labelledby="t-fuentes">
          <Revelar>
            <p className="kicker">02 · Fuentes y cortes</p>
            <h2 id="t-fuentes">La fecha de corte importa tanto como el valor</h2>
            <span className="cinta" aria-hidden="true" />
            <p>Cada variable conserva su fuente y su corte en el glosario y en la hoja «Diccionario» de cada descarga. Los cortes vigentes son:</p>
            <div className="cortes">
              {(meta?.sources ?? []).map((fuente) => (
                <div key={fuente.name}>
                  <strong>{fuente.name}</strong>
                  <span>{fuente.detail}</span>
                  <b>{fuente.cut}</b>
                </div>
              ))}
            </div>
          </Revelar>
        </section>

        <section aria-labelledby="t-definiciones">
          <Revelar>
            <p className="kicker">03 · Definiciones clave</p>
            <h2 id="t-definiciones">Las variables que más orientan la segmentación</h2>
            <span className="cinta" aria-hidden="true" />
            <p>
              Resumen de las definiciones institucionales más consultadas. El detalle completo, con todas las categorías, está en el <Link to="/glosario">glosario</Link>.
            </p>
          </Revelar>
          <div className="definiciones">
            {claves.map((entrada, i) => (
              <Revelar key={entrada.variable} retraso={i * 50}>
                <Definicion entrada={entrada} />
              </Revelar>
            ))}
          </div>
        </section>

        <section aria-labelledby="t-limites">
          <Revelar>
            <p className="kicker">04 · Alcance y límites</p>
            <h2 id="t-limites">Lo que la herramienta no pretende reemplazar</h2>
            <span className="cinta" aria-hidden="true" />
          </Revelar>
          <ul className="limites">
            {[
              ['No sustituye el criterio del asesor.', 'La información es cuantitativa; la segmentación final combina estos datos con aspectos cualitativos y conocimiento del sector.'],
              ['No reemplaza otras bases o análisis.', 'Complementa las herramientas de la Gerencia de Inteligencia Comercial y los análisis de la Vicepresidencia de Planeación.'],
              ['Los servicios no equivalen al universo nacional.', 'Las cifras de exportación de servicios provienen de negocios reportados a ProColombia y no representan el total exportado por el país.'],
              ['La disponibilidad cambia por variable.', 'Consulte siempre la fuente y el corte incluidos en el glosario y en el diccionario de la descarga.'],
              ['Los datos de contacto son de uso institucional.', 'Dirección, teléfono, correo y representante legal se entregan para la gestión comercial interna, según las políticas de tratamiento de información.'],
              ['La descarga tiene un límite por archivo.', `Hasta ${(meta?.export_max_rows ?? 5000).toLocaleString('es-CO')} empresas por Excel para garantizar un archivo manejable; refine los filtros si el universo es mayor.`],
            ].map(([titulo, texto], i) => (
              <Revelar key={titulo} retraso={i * 50}>
                <li>
                  <strong>{titulo}</strong>
                  <span>{texto}</span>
                </li>
              </Revelar>
            ))}
          </ul>
        </section>

        <section aria-labelledby="t-transferencia">
          <Revelar>
            <div className="transferencia">
              <div>
                <p className="kicker">05 · Transferencia técnica</p>
                <h2 id="t-transferencia">Un proyecto preparado para continuar</h2>
                <p>
                  Interfaz React + TypeScript, API FastAPI que conserva las consultas a Snowflake, y un único contenedor Docker que compila y sirve todo desde el mismo origen en Railway. La configuración vive en variables
                  de entorno; el código no contiene credenciales.
                </p>
                <p className="chico" style={{ color: '#9db1bf' }}>
                  Versión {meta?.version ?? '3.1.0'} · La guía completa está en el README y en GUIA_TRANSFERENCIA.md del repositorio.
                </p>
              </div>
              <ol>
                <li>
                  <span className="dato">1</span>Suba el repositorio y cree el servicio en Railway (detecta <code>railway.toml</code> y el <code>Dockerfile</code>).
                </li>
                <li>
                  <span className="dato">2</span>Configure las variables de Snowflake (<code>SF_*</code>) y, si lo desea, usuario y contraseña de acceso.
                </li>
                <li>
                  <span className="dato">3</span>Verifique <code>/api/health?deep=true</code>, una búsqueda y una descarga.
                </li>
                <li>
                  <span className="dato">4</span>Con cada nuevo corte, actualice sólo <code>backend/config.py</code> y el glosario en <code>backend/resources</code>.
                </li>
              </ol>
            </div>
          </Revelar>
        </section>
      </div>
    </>
  );
}
