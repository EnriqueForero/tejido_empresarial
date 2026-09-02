/**
 * Resultados de la consulta: conteo, descarga, búsqueda local, selección de
 * columnas, orden por columna, tabla con encabezado y columnas fijas
 * (escritorio) y tarjetas (móvil), paginación con tamaño de página.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { esNumericaVisual, etiquetaCorta, formatearValor } from '../formato';
import { useCerrarAlExterior, useDebounce } from '../hooks';
import type { Fila, RespuestaBusqueda, SolicitudBusqueda } from '../tipos';
import { DescargaExcel } from './DescargaExcel';
import { Aviso, EstadoVacio, Spinner } from './Interfaz';

type Props = {
  datos: RespuestaBusqueda;
  solicitud: SolicitudBusqueda;
  sucio: boolean;
  cargando: boolean;
  limiteExportacion: number;
  maxVistaPrevia: number;
  alPaginar: (pagina: number) => void;
  alCambiarTamano: (tamano: number) => void;
};

const ESENCIALES = ['NIT', 'Razón social'];
const SI_NO = new Set(['¿La empresa ha exportado?', 'Inversión extranjera', 'Empresa exportadora NME según actividad económica']);
const TAMANOS = [25, 50, 100];

function celda(valor: unknown, columna: string) {
  if (SI_NO.has(columna) && (valor === 'Sí' || valor === 'No')) {
    return <span className={`si-no si-no--${valor === 'Sí' ? 'si' : 'no'}`}>{valor}</span>;
  }
  return formatearValor(valor, columna);
}

export function Resultados({ datos, solicitud, sucio, cargando, limiteExportacion, maxVistaPrevia, alPaginar, alCambiarTamano }: Props) {
  const [columnas, setColumnas] = useState<string[]>(datos.columns);
  const [busqueda, setBusqueda] = useState('');
  const busquedaLenta = useDebounce(busqueda, 160);
  const [orden, setOrden] = useState<{ columna: string; direccion: 'asc' | 'desc' } | null>(null);
  const [menuColumnas, setMenuColumnas] = useState(false);
  const [paginaEditada, setPaginaEditada] = useState(String(datos.page));
  const menuRef = useRef<HTMLDivElement>(null);
  const identidad = useMemo(() => JSON.stringify({ m: solicitud.mode, f: solicitud.filters, t: solicitud.term, n: solicitud.nits }), [solicitud]);
  const identidadPrevia = useRef(identidad);

  useEffect(() => {
    if (identidadPrevia.current !== identidad) {
      identidadPrevia.current = identidad;
      setColumnas(datos.columns);
      setBusqueda('');
      setOrden(null);
      setMenuColumnas(false);
    } else {
      setColumnas((actuales) => {
        const disponibles = actuales.filter((columna) => datos.columns.includes(columna));
        const esenciales = ESENCIALES.filter((columna) => datos.columns.includes(columna) && !disponibles.includes(columna));
        return [...esenciales, ...disponibles];
      });
    }
  }, [datos.columns, identidad]);
  useEffect(() => setPaginaEditada(String(datos.page)), [datos.page]);
  useCerrarAlExterior(menuColumnas, menuRef, () => setMenuColumnas(false));

  const filas = useMemo(() => {
    const termino = busquedaLenta.trim().toLocaleLowerCase('es-CO');
    let lista: Fila[] = datos.rows;
    if (termino) lista = lista.filter((fila) => columnas.some((columna) => String(fila[columna] ?? '').toLocaleLowerCase('es-CO').includes(termino)));
    if (orden) {
      const { columna, direccion } = orden;
      const factor = direccion === 'asc' ? 1 : -1;
      lista = [...lista].sort((a, b) => {
        const va = a[columna];
        const vb = b[columna];
        if (va === null || va === undefined || va === '') return 1;
        if (vb === null || vb === undefined || vb === '') return -1;
        if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * factor;
        return String(va).localeCompare(String(vb), 'es-CO', { numeric: true, sensitivity: 'base' }) * factor;
      });
    }
    return lista;
  }, [datos.rows, busquedaLenta, columnas, orden]);

  const columnasTarjeta = columnas.filter((columna) => !ESENCIALES.includes(columna));
  const demasiadoGrande = datos.total > limiteExportacion;
  const motivoDescarga = sucio ? 'Cambió los criterios: actualice la búsqueda antes de descargar.' : demasiadoGrande ? `Supera las ${limiteExportacion.toLocaleString('es-CO')} empresas por archivo. Agregue filtros para habilitar la descarga.` : undefined;
  const desde = (datos.page - 1) * datos.page_size + 1;
  const hasta = Math.min(datos.total, datos.page * datos.page_size);

  const ordenarPor = (columna: string) =>
    setOrden((actual) => (actual?.columna === columna ? (actual.direccion === 'asc' ? { columna, direccion: 'desc' } : null) : { columna, direccion: 'asc' }));

  if (!datos.total) {
    return (
      <section className="resultados" id="resultados" aria-labelledby="titulo-resultados">
        <EstadoVacio titulo="No encontramos empresas con este criterio" texto="Pruebe con una razón social más corta, revise el NIT o retire alguno de los filtros. Los filtros se cruzan entre sí: cuanto más agregue, más pequeño será el segmento." />
      </section>
    );
  }

  return (
    <section className="resultados" id="resultados" aria-labelledby="titulo-resultados">
      <div className="resultados__cabecera">
        <div className="resultados__titulo">
          <p className="kicker">Paso 3 · Resultados</p>
          <h2 id="titulo-resultados" tabIndex={-1}>
            <span className="dato">{datos.total.toLocaleString('es-CO')}</span> {datos.total === 1 ? 'empresa encontrada' : 'empresas encontradas'}
          </h2>
          <p className="resultados__resumen">
            Criterio: <strong>{datos.summary}</strong> · mostrando {desde.toLocaleString('es-CO')}–{hasta.toLocaleString('es-CO')} · ordenadas por ingresos operacionales
          </p>
        </div>
        <DescargaExcel solicitud={solicitud} total={datos.total} deshabilitado={Boolean(motivoDescarga) || cargando} motivo={motivoDescarga} unaEmpresa={datos.total === 1} />
      </div>

      <div className="resultados__avisos">
        {sucio && <Aviso tipo="advertencia">Cambió los criterios de búsqueda. Los resultados en pantalla corresponden a la consulta anterior; pulse «Buscar» para actualizarlos.</Aviso>}
        {datos.preview_truncated && (
          <Aviso tipo="info">
            En pantalla se navegan las primeras {maxVistaPrevia.toLocaleString('es-CO')} empresas para mantener la respuesta ágil. Refine los filtros o descargue el archivo para trabajar el segmento completo.
          </Aviso>
        )}
        {datos.demo && <Aviso tipo="info">Modo de demostración: los registros son sintéticos y no corresponden a empresas reales.</Aviso>}
      </div>

      <div className="barra-tabla">
        <label className="campo-con-icono barra-tabla__buscar">
          <span className="sr-solo">Buscar dentro de esta página de resultados</span>
          <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
            <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
            <path d="m10.5 10.5 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <input className="campo" value={busqueda} onChange={(evento) => setBusqueda(evento.target.value)} placeholder="Buscar en esta página…" />
        </label>
        <div className="barra-tabla__acciones">
          <label className="selector-tamano">
            Por página
            <select value={datos.page_size} onChange={(evento) => alCambiarTamano(Number(evento.target.value))} disabled={cargando}>
              {TAMANOS.map((tamano) => (
                <option key={tamano} value={tamano}>
                  {tamano}
                </option>
              ))}
            </select>
          </label>
          <div className="columnas" ref={menuRef}>
            <button type="button" className="boton boton--fantasma boton--chico" aria-expanded={menuColumnas} aria-controls="menu-columnas" onClick={() => setMenuColumnas((valor) => !valor)}>
              Columnas · {columnas.length}
            </button>
            {menuColumnas && (
              <div id="menu-columnas" className="columnas__menu">
                <header>
                  <strong>Columnas visibles</strong>
                  <small>NIT y razón social siempre se muestran</small>
                </header>
                <div style={{ display: 'flex', gap: 10, marginBottom: 6 }}>
                  <button type="button" className="enlace-boton" onClick={() => setColumnas(datos.columns)}>
                    Todas
                  </button>
                  <button type="button" className="enlace-boton" onClick={() => setColumnas(ESENCIALES.filter((c) => datos.columns.includes(c)))}>
                    Sólo esenciales
                  </button>
                </div>
                {datos.columns.map((columna) => {
                  const esencial = ESENCIALES.includes(columna);
                  return (
                    <label key={columna} className={esencial ? 'esencial' : ''}>
                      <input
                        className="casilla"
                        type="checkbox"
                        checked={esencial || columnas.includes(columna)}
                        disabled={esencial}
                        onChange={() => setColumnas((actuales) => (actuales.includes(columna) ? actuales.filter((item) => item !== columna) : datos.columns.filter((c) => c === columna || actuales.includes(c))))}
                      />
                      <span>
                        {columna}
                        {esencial && <small> · esencial</small>}
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="tabla-resultados" tabIndex={0} aria-label="Tabla de resultados; desplácese horizontalmente para ver más columnas">
        <table>
          <thead>
            <tr>
              {columnas.map((columna, indice) => {
                const numerica = datos.rows.some((fila) => esNumericaVisual(columna, fila[columna]));
                const activo = orden?.columna === columna;
                return (
                  <th key={columna} scope="col" className={`${numerica ? 'num' : ''} ${indice === 0 ? 'fijo-1' : indice === 1 ? 'fijo-2' : ''}`} aria-sort={activo ? (orden?.direccion === 'asc' ? 'ascending' : 'descending') : 'none'}>
                    <button type="button" onClick={() => ordenarPor(columna)} title={`Ordenar por ${columna}`}>
                      <span>{etiquetaCorta(columna)}</span>
                      <span className="orden" aria-hidden="true">
                        {activo ? (orden?.direccion === 'asc' ? '▲' : '▼') : '↕'}
                      </span>
                    </button>
                  </th>
                );
              })}
              <th scope="col" className="acciones-fila">
                <span style={{ display: 'block', padding: '11px' }}>Ficha</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {filas.map((fila, indiceFila) => {
              const nit = String(fila.NIT ?? '');
              return (
                <tr key={`${nit}-${indiceFila}`}>
                  {columnas.map((columna, indice) => {
                    const numerica = esNumericaVisual(columna, fila[columna]);
                    const clase = `${numerica ? 'num dato' : ''} ${indice === 0 ? 'fijo-1 dato' : indice === 1 ? 'fijo-2' : ''}`.trim();
                    if (columna === 'Razón social' && nit) {
                      return (
                        <td key={columna} className={clase}>
                          <Link className="enlace-empresa" to={`/empresa/${nit}`}>
                            {String(fila[columna] ?? '—')}
                          </Link>
                        </td>
                      );
                    }
                    return (
                      <td key={columna} className={clase}>
                        {celda(fila[columna], columna)}
                      </td>
                    );
                  })}
                  <td className="acciones-fila">
                    {nit ? (
                      <Link className="boton boton--fantasma boton--chico" to={`/empresa/${nit}`}>
                        Ver ficha
                      </Link>
                    ) : (
                      '—'
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="tarjetas-resultados">
        {filas.map((fila, indiceFila) => {
          const nit = String(fila.NIT ?? '');
          return (
            <article key={`${nit}-t-${indiceFila}`} className="tarjeta-empresa">
              <div className="tarjeta-empresa__cab">
                <span className="dato">NIT {nit || '—'}</span>
                {fila['Tamaño de la empresa'] && <span className="etiqueta-mini etiqueta-mini--azul">{String(fila['Tamaño de la empresa'])}</span>}
              </div>
              <h3>{nit ? <Link to={`/empresa/${nit}`}>{String(fila['Razón social'] ?? '—')}</Link> : String(fila['Razón social'] ?? '—')}</h3>
              {columnasTarjeta.length > 0 && (
                <dl>
                  {columnasTarjeta.map((columna) => (
                    <div key={columna}>
                      <dt>{etiquetaCorta(columna)}</dt>
                      <dd className={esNumericaVisual(columna, fila[columna]) ? 'dato' : ''}>{celda(fila[columna], columna)}</dd>
                    </div>
                  ))}
                </dl>
              )}
              {nit && (
                <div className="tarjeta-empresa__pie">
                  <Link className="boton boton--fantasma boton--chico" to={`/empresa/${nit}`}>
                    Ver ficha completa →
                  </Link>
                </div>
              )}
            </article>
          );
        })}
      </div>

      {!filas.length && busqueda && <EstadoVacio titulo="No hay coincidencias en esta página" texto="La búsqueda local sólo revisa las empresas de la página actual. Pruebe otra palabra o borre el texto." />}

      {datos.page_count > 1 && (
        <nav className="paginacion" aria-label="Paginación de resultados">
          <button type="button" className="boton boton--fantasma boton--chico" disabled={cargando || datos.page <= 1} onClick={() => alPaginar(datos.page - 1)}>
            ← Anterior
          </button>
          <form
            className="paginacion__pagina"
            onSubmit={(evento) => {
              evento.preventDefault();
              const objetivo = Math.min(Math.max(1, Number(paginaEditada) || 1), datos.page_count);
              if (objetivo !== datos.page) alPaginar(objetivo);
              else setPaginaEditada(String(datos.page));
            }}
          >
            <span>Página</span>
            <input className="campo dato" inputMode="numeric" aria-label="Ir a la página" value={paginaEditada} onChange={(evento) => setPaginaEditada(evento.target.value.replace(/\D/g, ''))} onBlur={(evento) => evento.currentTarget.form?.requestSubmit()} />
            <span className="dato">/ {datos.page_count.toLocaleString('es-CO')}</span>
          </form>
          <button type="button" className="boton boton--fantasma boton--chico" disabled={cargando || datos.page >= datos.page_count} onClick={() => alPaginar(datos.page + 1)}>
            Siguiente →
          </button>
          {cargando && (
            <span className="paginacion__estado">
              <Spinner oscuro /> Cargando…
            </span>
          )}
        </nav>
      )}
    </section>
  );
}
