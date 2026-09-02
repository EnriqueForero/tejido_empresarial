/**
 * Página de consulta. Cuatro modos (filtros, razón social, NIT, lote de NIT),
 * filtros dependientes, resultados paginados y descarga Excel. La consulta
 * activa se refleja en la URL (?modo=…&q=…&f=CLAVE|valor) para compartirla.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { buscarEmpresas, ErrorApi, obtenerMetadatos, obtenerOpcionesFiltros } from '../api';
import { CargaNits } from '../componentes/CargaNits';
import { Aviso, CabeceraPagina, Spinner } from '../componentes/Interfaz';
import { ModoBusqueda } from '../componentes/ModoBusqueda';
import { PanelFiltros } from '../componentes/PanelFiltros';
import { Resultados } from '../componentes/Resultados';
import { limpiarNit } from '../formato';
import type { DefinicionFiltro, Metadatos, ModoBusqueda as Modo, RespuestaBusqueda, SolicitudBusqueda } from '../tipos';

const MODOS_VALIDOS: Modo[] = ['filters', 'business_name', 'nit', 'batch_nits'];

function construirSolicitud(modo: Modo, filtros: Record<string, string[]>, termino: string, nits: string[], pagina: number, tamano: number): SolicitudBusqueda {
  return {
    mode: modo,
    filters: modo === 'filters' ? Object.fromEntries(Object.entries(filtros).filter(([, valores]) => valores.length)) : {},
    term: modo === 'business_name' || modo === 'nit' ? termino.trim() : '',
    nits: modo === 'batch_nits' ? nits : [],
    page: pagina,
    page_size: tamano,
  };
}

export default function Consultar() {
  const [parametros, setParametros] = useSearchParams();
  const [meta, setMeta] = useState<Metadatos | null>(null);
  const [definiciones, setDefiniciones] = useState<DefinicionFiltro[]>([]);
  const [modo, setModo] = useState<Modo>(() => (MODOS_VALIDOS.includes(parametros.get('modo') as Modo) ? (parametros.get('modo') as Modo) : 'filters'));
  const [filtros, setFiltros] = useState<Record<string, string[]>>(() => {
    const iniciales: Record<string, string[]> = {};
    parametros.getAll('f').forEach((par) => {
      const [clave, ...resto] = par.split('|');
      const valor = resto.join('|');
      if (clave && valor) iniciales[clave] = [...(iniciales[clave] ?? []), valor];
    });
    return iniciales;
  });
  const [termino, setTermino] = useState(() => parametros.get('q') ?? '');
  const [nits, setNits] = useState<string[]>([]);
  const [tamano, setTamano] = useState(25);
  const [resultados, setResultados] = useState<RespuestaBusqueda | null>(null);
  const [solicitudActiva, setSolicitudActiva] = useState<SolicitudBusqueda | null>(null);
  const [cargando, setCargando] = useState(false);
  const [cargandoOpciones, setCargandoOpciones] = useState(false);
  const [error, setError] = useState('');
  const [errorOpciones, setErrorOpciones] = useState('');
  const [sucio, setSucio] = useState(false);
  const [cajonMovil, setCajonMovil] = useState(false);
  const controladorRef = useRef<AbortController | null>(null);
  const secuenciaRef = useRef(0);
  const busquedaInicialRef = useRef(Boolean(parametros.get('modo') || parametros.get('q') || parametros.getAll('f').length));

  useEffect(() => {
    obtenerMetadatos()
      .then((datos) => {
        setMeta(datos);
        setDefiniciones(datos.filters);
      })
      .catch((razon: unknown) => setError(razon instanceof ErrorApi ? razon.message : 'No fue posible cargar la configuración del aplicativo.'));
  }, []);

  // Opciones dependientes: se recalculan al cambiar cualquier selección.
  useEffect(() => {
    if (modo !== 'filters') return;
    const controlador = new AbortController();
    const temporizador = window.setTimeout(() => {
      setCargandoOpciones(true);
      obtenerOpcionesFiltros(filtros, controlador.signal)
        .then((respuesta) => {
          setDefiniciones(respuesta.filters);
          setErrorOpciones('');
        })
        .catch((razon: unknown) => {
          if (razon instanceof DOMException && razon.name === 'AbortError') return;
          // El aviso va dentro del panel: es ahí donde se nota que no hay opciones.
          setErrorOpciones(razon instanceof ErrorApi ? razon.message : 'No fue posible cargar los filtros.');
        })
        .finally(() => {
          if (!controlador.signal.aborted) setCargandoOpciones(false);
        });
    }, 220);
    return () => {
      window.clearTimeout(temporizador);
      controlador.abort();
    };
  }, [filtros, modo]);

  useEffect(() => {
    const punto = window.matchMedia('(max-width: 980px)');
    const cerrar = (evento: MediaQueryListEvent) => {
      if (!evento.matches) setCajonMovil(false);
    };
    punto.addEventListener('change', cerrar);
    return () => punto.removeEventListener('change', cerrar);
  }, []);

  useEffect(() => () => controladorRef.current?.abort(), []);

  const marcarCambio = useCallback(() => {
    controladorRef.current?.abort();
    controladorRef.current = null;
    secuenciaRef.current += 1;
    setCargando(false);
    if (resultados) setSucio(true);
  }, [resultados]);

  const activos = useMemo(
    () => Object.entries(filtros).flatMap(([clave, valores]) => valores.map((valor) => ({ clave, valor, etiqueta: definiciones.find((d) => d.key === clave)?.label ?? clave }))),
    [filtros, definiciones],
  );

  const sincronizarUrl = (solicitud: SolicitudBusqueda) => {
    const siguientes = new URLSearchParams();
    siguientes.set('modo', solicitud.mode);
    if (solicitud.term) siguientes.set('q', solicitud.term);
    Object.entries(solicitud.filters).forEach(([clave, valores]) => valores.forEach((valor) => siguientes.append('f', `${clave}|${valor}`)));
    setParametros(siguientes, { replace: true });
  };

  const ejecutar = useCallback(
    async (pagina = 1, tamanoPagina = tamano) => {
      const solicitud = construirSolicitud(modo, filtros, termino, nits, pagina, tamanoPagina);
      controladorRef.current?.abort();
      const controlador = new AbortController();
      controladorRef.current = controlador;
      const secuencia = ++secuenciaRef.current;
      setCargando(true);
      setError('');
      try {
        const respuesta = await buscarEmpresas(solicitud, controlador.signal);
        if (secuencia !== secuenciaRef.current) return;
        setResultados(respuesta);
        setSolicitudActiva(solicitud);
        setSucio(false);
        setCajonMovil(false);
        if (solicitud.mode !== 'batch_nits') sincronizarUrl(solicitud);
        window.setTimeout(() => {
          document.getElementById('resultados')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
          document.getElementById('titulo-resultados')?.focus({ preventScroll: true });
        }, 40);
      } catch (razon) {
        if (razon instanceof DOMException && razon.name === 'AbortError') return;
        if (secuencia === secuenciaRef.current) setError(razon instanceof ErrorApi ? razon.message : 'No fue posible completar la búsqueda.');
      } finally {
        if (secuencia === secuenciaRef.current) setCargando(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [modo, filtros, termino, nits, tamano],
  );

  // Consulta compartida por URL: se ejecuta una vez al entrar.
  useEffect(() => {
    if (!busquedaInicialRef.current || !meta) return;
    busquedaInicialRef.current = false;
    const solicitudValida = modo === 'filters' || ((modo === 'business_name' || modo === 'nit') && termino.trim().length >= 2);
    if (solicitudValida) void ejecutar(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meta]);

  const cambiarModo = (siguiente: Modo) => {
    marcarCambio();
    setModo(siguiente);
    setError('');
    setResultados(null);
    setSolicitudActiva(null);
    setSucio(false);
    setTermino('');
    setNits([]);
    setParametros(new URLSearchParams(), { replace: true });
  };
  const actualizarFiltro = (clave: string, valores: string[]) => {
    marcarCambio();
    setFiltros((actuales) => {
      const siguientes = { ...actuales };
      if (valores.length) siguientes[clave] = valores;
      else delete siguientes[clave];
      return siguientes;
    });
  };
  const limpiarFiltros = () => {
    marcarCambio();
    setFiltros({});
  };

  const valido = modo === 'filters' || (modo === 'business_name' && termino.trim().length >= 2) || (modo === 'nit' && limpiarNit(termino).length >= 2) || (modo === 'batch_nits' && nits.length > 0);
  const conexion = meta?.data_connection;

  return (
    <>
      <CabeceraPagina
        oscura
        kicker="Tejido Empresarial · Consulta"
        titulo={<>Encuentre la empresa o el segmento que necesita.</>}
        bajada="Elija una forma de búsqueda, revise una vista previa legible y descargue un Excel con todo el detalle. Puede cambiar de modo sin perder la página."
        lateral={
          meta && (
            <>
              <span className="etiqueta-mini etiqueta-mini--acento dato">{meta.periods.companies}</span>
              <span className="etiqueta-mini etiqueta-mini--acento dato">{meta.periods.exports}</span>
            </>
          )
        }
      />
      <div className="pagina consulta">
        {conexion === 'missing_configuration' && (
          <div className="consulta__aviso">
            <Aviso tipo="advertencia">La interfaz está lista, pero falta configurar la conexión segura a Snowflake en este entorno. Consulte el README para las variables requeridas.</Aviso>
          </div>
        )}
        {conexion === 'demo' && (
          <div className="consulta__aviso">
            <Aviso tipo="info">Modo de demostración: los datos son sintéticos y sirven únicamente para recorrer la experiencia.</Aviso>
          </div>
        )}

        <section aria-labelledby="titulo-modo">
          <p className="kicker">Paso 1 · Tipo de consulta</p>
          <h2 id="titulo-modo" className="mt-8" style={{ marginBottom: 14 }}>
            ¿Cómo quiere buscar?
          </h2>
          <ModoBusqueda modo={modo} alCambiar={cambiarModo} />
        </section>

        {modo === 'filters' ? (
          <section className="espacio" aria-label="Segmentación por filtros">
            <PanelFiltros
              definiciones={definiciones}
              ordenGrupos={meta?.filter_groups ?? []}
              filtros={filtros}
              alCambiar={actualizarFiltro}
              alLimpiar={limpiarFiltros}
              alBuscar={() => void ejecutar(1)}
              cargando={cargando}
              cargandoOpciones={cargandoOpciones}
              errorOpciones={errorOpciones}
              abiertoMovil={cajonMovil}
              alCerrarMovil={() => setCajonMovil(false)}
              totalActivos={activos.length}
            />
            <div>
              <div className="criterios">
                <div className="criterios__cab">
                  <div>
                    <p className="kicker">Criterios activos</p>
                    <h2>{activos.length ? `${activos.length} ${activos.length === 1 ? 'criterio' : 'criterios'} seleccionados` : 'Toda la base empresarial'}</h2>
                  </div>
                  {activos.length > 0 && (
                    <button type="button" className="enlace-boton" onClick={limpiarFiltros}>
                      Limpiar todo
                    </button>
                  )}
                </div>
                {activos.length ? (
                  <div className="criterios__lista">
                    {activos.map((item) => (
                      <button key={`${item.clave}-${item.valor}`} type="button" className="criterio" onClick={() => actualizarFiltro(item.clave, (filtros[item.clave] ?? []).filter((v) => v !== item.valor))} title={`Quitar ${item.valor}`}>
                        <span>
                          <small>{item.etiqueta}</small>
                          <strong>{item.valor}</strong>
                        </span>
                        <i aria-hidden="true">×</i>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="criterios__vacio">
                    <span aria-hidden="true">∞</span>
                    <p>
                      <strong>Sin restricciones todavía.</strong>
                      <br />
                      Use el panel de filtros para construir un segmento: ubicación, tamaño, actividad económica, trayectoria exportadora, sector, país de destino… O consulte toda la base.
                    </p>
                  </div>
                )}
                <div className="criterios__pie">
                  <div>
                    <strong>{activos.length ? 'Segmento listo para consultar' : 'Consulta general'}</strong>
                    <span>{activos.length ? 'Revise los criterios y obtenga la vista previa.' : `La descarga admite hasta ${(meta?.export_max_rows ?? 5000).toLocaleString('es-CO')} empresas; con toda la base necesitará filtros para descargar.`}</span>
                  </div>
                  <button type="button" className="boton boton--cinta boton--xl" onClick={() => void ejecutar(1)} disabled={cargando}>
                    {cargando ? (
                      <>
                        <Spinner oscuro /> Consultando…
                      </>
                    ) : (
                      <>
                        Buscar empresas <span className="boton__flecha" aria-hidden="true">→</span>
                      </>
                    )}
                  </button>
                </div>
                {meta && meta.notes.length > 0 && (
                  <details className="criterios__notas">
                    <summary>Notas sobre la definición de algunos filtros</summary>
                    <ul>
                      {meta.notes.map((nota) => (
                        <li key={nota}>{nota}</li>
                      ))}
                    </ul>
                  </details>
                )}
              </div>
              <button type="button" className="abrir-filtros boton boton--primario" onClick={() => setCajonMovil(true)}>
                Filtros · {activos.length}
              </button>
            </div>
          </section>
        ) : (
          <section className="directa" aria-label="Búsqueda directa">
            <div className="directa__texto">
              <p className="kicker">Paso 2 · Criterio</p>
              <h2>{modo === 'business_name' ? 'Escriba la razón social' : modo === 'nit' ? 'Escriba el NIT' : 'Cargue o pegue los NIT'}</h2>
              <p>
                {modo === 'business_name'
                  ? 'No necesita el nombre completo: buscamos coincidencias parciales sin distinguir mayúsculas ni tildes en la base.'
                  : modo === 'nit'
                    ? 'Puede escribir el NIT completo o una parte. Escriba sólo los dígitos, sin el dígito de verificación.'
                    : 'Un NIT por línea. Eliminamos duplicados, puntos y guiones antes de consultar.'}
              </p>
              {modo !== 'batch_nits' && (
                <div className="directa__ejemplos">
                  <span>Ejemplos:</span>
                  {(modo === 'business_name' ? ['tejidos', 'café', 'software'] : ['900000001', '900000003', '9000000']).map((ejemplo) => (
                    <button key={ejemplo} type="button" onClick={() => setTermino(ejemplo)}>
                      {ejemplo}
                    </button>
                  ))}
                </div>
              )}
            </div>
            {modo !== 'batch_nits' ? (
              <form
                className="formulario-directa"
                onSubmit={(evento) => {
                  evento.preventDefault();
                  if (valido) void ejecutar(1);
                }}
              >
                <label htmlFor="criterio-busqueda">{modo === 'business_name' ? 'Razón social' : 'NIT'}</label>
                <div className="formulario-directa__fila">
                  <input
                    id="criterio-busqueda"
                    className="campo campo--grande"
                    autoFocus
                    value={termino}
                    inputMode={modo === 'nit' ? 'numeric' : 'search'}
                    autoComplete="off"
                    onChange={(evento) => {
                      setTermino(evento.target.value);
                      marcarCambio();
                    }}
                    placeholder={modo === 'business_name' ? 'Ej. tecnología colombiana' : 'Ej. 900409346'}
                  />
                  <button className="boton boton--cinta boton--xl" type="submit" disabled={!valido || cargando}>
                    {cargando ? (
                      <>
                        <Spinner oscuro /> Buscando…
                      </>
                    ) : (
                      'Buscar'
                    )}
                  </button>
                </div>
                <small>{modo === 'business_name' ? 'Sugerencia: empiece por la palabra más distintiva del nombre. Mínimo dos caracteres.' : 'Los resultados conservan el NIT como identificador de texto, con sus ceros iniciales.'}</small>
              </form>
            ) : (
              <CargaNits
                nits={nits}
                maximo={meta?.batch_max_nits ?? 5000}
                alCambiar={(lista) => {
                  setNits(lista);
                  marcarCambio();
                }}
                alConsultar={() => void ejecutar(1)}
                cargando={cargando}
              />
            )}
          </section>
        )}

        {error && (
          <div className="mt-16">
            <Aviso tipo="error">{error}</Aviso>
          </div>
        )}

        {resultados && solicitudActiva && (
          <Resultados
            datos={resultados}
            solicitud={solicitudActiva}
            sucio={sucio}
            cargando={cargando}
            limiteExportacion={meta?.export_max_rows ?? 5000}
            maxVistaPrevia={meta?.preview_max_rows ?? 10000}
            alPaginar={(pagina) => void ejecutar(pagina)}
            alCambiarTamano={(nuevo) => {
              setTamano(nuevo);
              void ejecutar(1, nuevo);
            }}
          />
        )}

        {!resultados && !cargando && (
          <section className="orientacion" aria-label="Qué verá después de buscar">
            <span className="orientacion__num dato" aria-hidden="true">
              03
            </span>
            <div>
              <h2>Los resultados aparecerán aquí</h2>
              <p>Una vista previa legible con las variables esenciales, la ficha completa de cada empresa y la descarga Excel en un solo paso.</p>
            </div>
            <dl>
              <div>
                <dt>Vista previa</dt>
                <dd>{meta?.preview_columns.length ?? 15} variables clave · 25 a 100 por página</dd>
              </div>
              <div>
                <dt>Ficha de empresa</dt>
                <dd>{meta?.export_columns.length ?? 63} variables por secciones</dd>
              </div>
              <div>
                <dt>Excel</dt>
                <dd>Resumen, datos y diccionario</dd>
              </div>
            </dl>
          </section>
        )}
        {cargando && !resultados && (
          <div className="estado-carga" role="status">
            <Spinner oscuro /> Consultando la base empresarial…
          </div>
        )}

        {meta && (
          <p className="nota-fuentes">
            Fuentes: {meta.sources.map((f) => `${f.name} (${f.cut})`).join(' · ')}. {meta.notes[0]} Las descargas admiten hasta {meta.export_max_rows.toLocaleString('es-CO')} empresas por archivo.
          </p>
        )}
      </div>
    </>
  );
}
