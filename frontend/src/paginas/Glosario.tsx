/**
 * Glosario de variables: lectura estructurada del archivo institucional
 * «2026_09_01_Glosario_variables - Aplicativo.xlsx». Búsqueda, categorías,
 * fichas expandibles con descripción, fuente y dónde se usa cada variable.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ErrorApi, obtenerGlosario } from '../api';
import { Aviso, CabeceraPagina, EstadoVacio, IconoArchivo, Pastilla, Spinner } from '../componentes/Interfaz';
import type { EntradaGlosario, RespuestaGlosario } from '../tipos';

function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('es-CO');
}

function idDe(variable: string) {
  return `v-${normalizar(variable).replace(/[^a-z0-9]+/g, '-')}`;
}

/** Las descripciones largas del glosario enumeran categorías separadas por saltos de línea. */
function Descripcion({ entrada }: { entrada: EntradaGlosario }) {
  const parrafos = entrada.description_paragraphs.length ? entrada.description_paragraphs : [entrada.description];
  if (parrafos.length === 1) return <p>{parrafos[0]}</p>;
  const [intro, ...resto] = parrafos;
  const items = resto.map((linea) => {
    const separador = linea.indexOf(':');
    if (separador > 0 && separador < 70) return { titulo: linea.slice(0, separador).trim(), texto: linea.slice(separador + 1).trim() };
    return { titulo: '', texto: linea };
  });
  return (
    <>
      <p>{intro}</p>
      <ul>
        {items.map((item, i) => (
          <li key={i}>
            {item.titulo && <strong>{item.titulo}: </strong>}
            {item.texto}
          </li>
        ))}
      </ul>
    </>
  );
}

export default function Glosario() {
  const [parametros] = useSearchParams();
  const [datos, setDatos] = useState<RespuestaGlosario | null>(null);
  const [error, setError] = useState('');
  const [consulta, setConsulta] = useState('');
  const [categoria, setCategoria] = useState('Todas');
  const [abiertas, setAbiertas] = useState<Set<string>>(new Set());
  const destacada = parametros.get('v');
  const enfocada = useRef(false);

  useEffect(() => {
    obtenerGlosario()
      .then(setDatos)
      .catch((razon: unknown) => setError(razon instanceof ErrorApi ? razon.message : 'No fue posible cargar el glosario.'));
  }, []);

  useEffect(() => {
    if (!datos || !destacada || enfocada.current) return;
    enfocada.current = true;
    setAbiertas(new Set([destacada]));
    window.setTimeout(() => document.getElementById(idDe(destacada))?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 60);
  }, [datos, destacada]);

  const entradas = useMemo(() => {
    if (!datos) return [];
    const termino = normalizar(consulta.trim());
    return datos.entries.filter((entrada) => (categoria === 'Todas' || entrada.category === categoria) && (!termino || normalizar(`${entrada.variable} ${entrada.description} ${entrada.sources}`).includes(termino)));
  }, [datos, consulta, categoria]);

  const alternar = (variable: string) =>
    setAbiertas((actual) => {
      const siguiente = new Set(actual);
      if (siguiente.has(variable)) siguiente.delete(variable);
      else siguiente.add(variable);
      return siguiente;
    });

  return (
    <>
      <CabeceraPagina
        oscura
        kicker={`Glosario de variables · actualizado ${datos?.updated_at ?? '2026-09-01'}`}
        titulo="Entienda cada variable antes de usarla."
        bajada={
          <>
            Definiciones, alcance y fuentes del archivo institucional <strong>{datos?.file_name ?? '2026_09_01_Glosario_variables - Aplicativo.xlsx'}</strong>, organizadas por secciones y enlazadas con los filtros, la
            vista previa y la descarga. El mismo diccionario acompaña cada Excel que descargue.
          </>
        }
        lateral={
          <a className="boton boton--cinta" href="/api/resources/glossary.xlsx" download>
            <IconoArchivo tipo="XLSX" /> Descargar glosario original
          </a>
        }
      />
      <div className="pagina glosario">
        <aside className="glosario__indice tarjeta" aria-label="Buscar y filtrar el glosario">
          <label>
            <span>Variable o palabra clave</span>
            <div className="campo-con-icono">
              <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
                <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
                <path d="m10.5 10.5 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
              <input className="campo" value={consulta} onChange={(evento) => setConsulta(evento.target.value)} placeholder="Ej. trayectoria, ingresos, CIIU…" />
            </div>
          </label>
          <div className="categorias" role="group" aria-label="Secciones del glosario">
            {['Todas', ...(datos?.categories ?? [])].map((item) => (
              <button type="button" key={item} aria-pressed={categoria === item} onClick={() => setCategoria(item)}>
                {item}
                <span className="dato">{item === 'Todas' ? datos?.count ?? 0 : datos?.entries.filter((entrada) => entrada.category === item).length ?? 0}</span>
              </button>
            ))}
          </div>
          <div className="glosario__leyenda">
            <strong>Cómo leer cada ficha</strong>
            <span>
              <Pastilla tono="azul">Filtro</Pastilla> la variable puede usarse para segmentar. <Pastilla tono="acento">Vista previa</Pastilla> aparece en la tabla de resultados. <Pastilla tono="ok">Descarga</Pastilla> está en el Excel.
            </span>
            <span>Las variables marcadas como «definición complementaria» son rangos derivados que el aplicativo entrega; su definición proviene de la variable base.</span>
          </div>
        </aside>

        <section aria-labelledby="titulo-glosario-lista">
          <div className="glosario__resumen">
            <div>
              <p className="kicker">Resultados</p>
              <h2 id="titulo-glosario-lista">
                {datos ? entradas.length : '—'} {entradas.length === 1 ? 'variable' : 'variables'}
                {categoria !== 'Todas' ? ` · ${categoria}` : ''}
              </h2>
            </div>
            <div className="acciones">
              <button type="button" className="enlace-boton" onClick={() => setAbiertas(new Set(entradas.map((e) => e.variable)))} disabled={!entradas.length}>
                Expandir todo
              </button>
              <button type="button" className="enlace-boton" onClick={() => setAbiertas(new Set())} disabled={!abiertas.size}>
                Contraer todo
              </button>
            </div>
          </div>

          {!datos && !error && (
            <div className="estado-carga" role="status">
              <Spinner oscuro /> Cargando definiciones…
            </div>
          )}
          {error && <Aviso tipo="error">{error}</Aviso>}
          {datos && datos.coverage.missing.length > 0 && (
            <div className="mt-12">
              <Aviso tipo="advertencia">
                El glosario aún no define {datos.coverage.missing.length} columna(s) presentes en la descarga: {datos.coverage.missing.join(', ')}. En el Excel se marcan como pendientes de definición.
              </Aviso>
            </div>
          )}

          <div className="fichas">
            {entradas.map((entrada) => {
              const abierta = abiertas.has(entrada.variable);
              return (
                <details
                  key={entrada.variable}
                  id={idDe(entrada.variable)}
                  className={`ficha-variable ${destacada === entrada.variable ? 'ficha-variable--destacada' : ''}`}
                  open={abierta}
                  onToggle={(evento) => {
                    const abiertoAhora = (evento.currentTarget as HTMLDetailsElement).open;
                    if (abiertoAhora !== abierta) alternar(entrada.variable);
                  }}
                >
                  <summary>
                    <span className="ficha-variable__nombre">
                      <small>{entrada.category}</small>
                      <strong>{entrada.variable}</strong>
                      <span className="ficha-variable__usos">
                        {entrada.filter_key && <Pastilla tono="azul">Filtro</Pastilla>}
                        {entrada.in_preview && <Pastilla tono="acento">Vista previa</Pastilla>}
                        {entrada.in_export && <Pastilla tono="ok">Descarga</Pastilla>}
                        {entrada.origin === 'aplicativo' && <Pastilla>Definición complementaria</Pastilla>}
                      </span>
                    </span>
                    <span className="ficha-variable__mas" aria-hidden="true">
                      +
                    </span>
                  </summary>
                  <div className="ficha-variable__cuerpo">
                    <div>
                      <h3>Qué significa</h3>
                      <Descripcion entrada={entrada} />
                    </div>
                    <div className="ficha-variable__fuente">
                      <div>
                        <h3>Fuente y corte</h3>
                        <p>{entrada.sources}</p>
                      </div>
                      {entrada.filter_key && (
                        <div>
                          <h3>Filtro relacionado</h3>
                          <p>{entrada.filter_label}</p>
                          <Link to={`/consultar?modo=filters`}>Ir a segmentar →</Link>
                        </div>
                      )}
                    </div>
                  </div>
                </details>
              );
            })}
            {datos && !entradas.length && (
              <EstadoVacio titulo="No hay coincidencias" texto="Pruebe con otra palabra o seleccione «Todas» las secciones.">
                <button
                  type="button"
                  className="boton boton--fantasma boton--chico mt-12"
                  onClick={() => {
                    setConsulta('');
                    setCategoria('Todas');
                  }}
                >
                  Limpiar búsqueda
                </button>
              </EstadoVacio>
            )}
          </div>
        </section>
      </div>
    </>
  );
}
