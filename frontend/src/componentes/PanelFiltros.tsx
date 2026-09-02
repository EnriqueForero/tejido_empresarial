/**
 * Panel de filtros agrupados (dependientes entre sí). En escritorio es una
 * columna fija; en móvil, un cajón lateral modal con trampa de foco.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { useBloquearScroll, useTrampaFoco } from '../hooks';
import type { DefinicionFiltro } from '../tipos';
import { Spinner } from './Interfaz';
import { SelectorFiltro } from './SelectorFiltro';

type Props = {
  definiciones: DefinicionFiltro[];
  ordenGrupos: string[];
  filtros: Record<string, string[]>;
  alCambiar: (clave: string, valores: string[]) => void;
  alLimpiar: () => void;
  alBuscar: () => void;
  cargando: boolean;
  cargandoOpciones: boolean;
  abiertoMovil: boolean;
  alCerrarMovil: () => void;
  totalActivos: number;
};

export function PanelFiltros({ definiciones, ordenGrupos, filtros, alCambiar, alLimpiar, alBuscar, cargando, cargandoOpciones, abiertoMovil, alCerrarMovil, totalActivos }: Props) {
  const panelRef = useRef<HTMLElement>(null);
  const cerrarRef = useRef<HTMLButtonElement>(null);
  const [gruposCerrados, setGruposCerrados] = useState<Set<string>>(new Set());
  useBloquearScroll(abiertoMovil);
  useTrampaFoco(abiertoMovil, panelRef);

  useEffect(() => {
    if (!abiertoMovil) return;
    cerrarRef.current?.focus();
    const alTeclear = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') alCerrarMovil();
    };
    document.addEventListener('keydown', alTeclear);
    return () => document.removeEventListener('keydown', alTeclear);
  }, [abiertoMovil, alCerrarMovil]);

  const grupos = useMemo(() => {
    const mapa = new Map<string, DefinicionFiltro[]>();
    definiciones.forEach((definicion) => mapa.set(definicion.group, [...(mapa.get(definicion.group) ?? []), definicion]));
    const ordenados = ordenGrupos.filter((grupo) => mapa.has(grupo));
    [...mapa.keys()].forEach((grupo) => {
      if (!ordenados.includes(grupo)) ordenados.push(grupo);
    });
    return ordenados.map((grupo) => [grupo, mapa.get(grupo) ?? []] as const);
  }, [definiciones, ordenGrupos]);

  const alternarGrupo = (grupo: string) =>
    setGruposCerrados((actual) => {
      const siguiente = new Set(actual);
      if (siguiente.has(grupo)) siguiente.delete(grupo);
      else siguiente.add(grupo);
      return siguiente;
    });

  return (
    <>
      <aside
        ref={panelRef}
        className={`panel-filtros ${abiertoMovil ? 'panel-filtros--abierto' : ''}`}
        aria-label="Filtros de segmentación"
        role={abiertoMovil ? 'dialog' : undefined}
        aria-modal={abiertoMovil || undefined}
        aria-labelledby="titulo-panel-filtros"
      >
        <div className="panel-filtros__cabecera">
          <div>
            <p className="kicker" style={{ marginBottom: 4 }}>
              Paso 2 · Filtros
            </p>
            <h2 id="titulo-panel-filtros">Construya el segmento</h2>
            <p>Dentro de un filtro los valores se suman; entre filtros se cruzan. Las opciones se ajustan a lo que ya eligió.</p>
          </div>
          <button ref={cerrarRef} type="button" className="panel-filtros__cerrar" aria-label="Cerrar filtros" onClick={alCerrarMovil}>
            ×
          </button>
        </div>
        <div className="panel-filtros__estado" role="status" aria-live="polite">
          {cargandoOpciones ? (
            <>
              <Spinner oscuro /> Actualizando opciones disponibles…
            </>
          ) : totalActivos ? (
            <>
              <strong className="dato">{totalActivos}</strong> {totalActivos === 1 ? 'criterio activo' : 'criterios activos'}
            </>
          ) : (
            'Sin criterios: la consulta abarcará toda la base empresarial.'
          )}
        </div>
        <div className="panel-filtros__cuerpo">
          {grupos.map(([grupo, items]) => {
            const activos = items.reduce((suma, item) => suma + (filtros[item.key]?.length ?? 0), 0);
            const abierto = !gruposCerrados.has(grupo);
            const id = `grupo-${grupo.replace(/\s+/g, '-').toLowerCase()}`;
            return (
              <section key={grupo} className="grupo" aria-labelledby={`${id}-titulo`}>
                <button type="button" className="grupo__cab" id={`${id}-titulo`} aria-expanded={abierto} aria-controls={id} onClick={() => alternarGrupo(grupo)}>
                  <span>{grupo}</span>
                  <span className={`grupo__conteo ${activos ? 'grupo__conteo--activo' : ''}`}>{activos || items.length}</span>
                  <svg className="grupo__flecha" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
                    <path d="M3 5.5 7 9.5l4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </button>
                {abierto && (
                  <div className="grupo__cuerpo" id={id}>
                    {items.map((definicion) => (
                      <SelectorFiltro key={definicion.key} definicion={definicion} seleccion={filtros[definicion.key] ?? []} alCambiar={(valores) => alCambiar(definicion.key, valores)} />
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
        <div className="panel-filtros__acciones">
          <button type="button" className="enlace-boton" onClick={alLimpiar} disabled={!totalActivos}>
            Limpiar todo
          </button>
          <button type="button" className="boton boton--cinta" onClick={alBuscar} disabled={cargando}>
            {cargando ? (
              <>
                <Spinner oscuro /> Buscando…
              </>
            ) : (
              <>
                Buscar empresas <span className="boton__flecha" aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>
      </aside>
      {abiertoMovil && <button type="button" className="fondo-cajon" aria-label="Cerrar filtros" onClick={alCerrarMovil} />}
    </>
  );
}
