/**
 * Filtro de selección múltiple con búsqueda dentro de las opciones.
 * Sustituye el multiselect de Streamlit: el usuario ve el nombre del filtro,
 * cuántos valores eligió, puede buscar dentro de la lista, marcar/desmarcar
 * todo lo visible y retirar valores desde las fichas de selección.
 */
import { useId, useMemo, useState } from 'react';
import { Ayuda } from './Interfaz';
import type { DefinicionFiltro } from '../tipos';

const MAX_VISIBLES = 250;

type Props = {
  definicion: DefinicionFiltro;
  seleccion: string[];
  alCambiar: (valores: string[]) => void;
};

function normalizar(texto: string) {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLocaleLowerCase('es-CO');
}

export function SelectorFiltro({ definicion, seleccion, alCambiar }: Props) {
  const [abierto, setAbierto] = useState(false);
  const [consulta, setConsulta] = useState('');
  const idPanel = useId();
  const opcionesTodas = definicion.options ?? [];

  const opciones = useMemo(() => {
    const termino = normalizar(consulta.trim());
    const base = termino ? opcionesTodas.filter((valor) => normalizar(valor).includes(termino)) : opcionesTodas;
    // Los valores seleccionados que ya no están disponibles se muestran igual para poder retirarlos.
    const faltantes = seleccion.filter((valor) => !opcionesTodas.includes(valor) && (!termino || normalizar(valor).includes(termino)));
    return [...faltantes, ...base];
  }, [consulta, opcionesTodas, seleccion]);

  const visibles = opciones.slice(0, MAX_VISIBLES);
  const alternar = (valor: string) => alCambiar(seleccion.includes(valor) ? seleccion.filter((item) => item !== valor) : [...seleccion, valor]);
  const marcarVisibles = () => alCambiar([...new Set([...seleccion, ...visibles])]);
  const desmarcarVisibles = () => alCambiar(seleccion.filter((valor) => !visibles.includes(valor)));
  const todasVisiblesMarcadas = visibles.length > 0 && visibles.every((valor) => seleccion.includes(valor));

  return (
    <div className={`selector ${abierto ? 'selector--abierto' : ''} ${seleccion.length ? 'selector--activo' : ''}`}>
      <button type="button" className="selector__cab" aria-expanded={abierto} aria-controls={idPanel} onClick={() => setAbierto((valor) => !valor)}>
        <span className="selector__etiqueta">
          {definicion.label}
          {definicion.help && <Ayuda texto={definicion.help} etiqueta={definicion.label} />}
        </span>
        <span className={`selector__conteo ${seleccion.length ? 'selector__conteo--activo' : ''}`}>{seleccion.length ? seleccion.length : 'Todos'}</span>
        <svg className="selector__flecha" width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
          <path d="M3 5.5 7 9.5l4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {!abierto && seleccion.length > 0 && (
        <div className="selector__seleccion">
          {seleccion.slice(0, 4).map((valor) => (
            <button key={valor} type="button" onClick={() => alternar(valor)} title={`Quitar ${valor}`} aria-label={`Quitar ${valor} de ${definicion.label}`}>
              <span>{valor}</span>
              <i aria-hidden="true">×</i>
            </button>
          ))}
          {seleccion.length > 4 && (
            <button type="button" onClick={() => setAbierto(true)} aria-label={`Ver los ${seleccion.length} valores seleccionados`}>
              <span>+{seleccion.length - 4} más</span>
            </button>
          )}
        </div>
      )}

      {abierto && (
        <div className="selector__panel" id={idPanel}>
          <label className="campo-con-icono selector__buscar">
            <span className="sr-solo">Buscar dentro de {definicion.label}</span>
            <svg width="15" height="15" viewBox="0 0 16 16" aria-hidden="true">
              <circle cx="7" cy="7" r="4.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
              <path d="m10.5 10.5 3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
            <input className="campo" value={consulta} onChange={(evento) => setConsulta(evento.target.value)} placeholder={`Buscar en ${opcionesTodas.length.toLocaleString('es-CO')} opciones…`} autoFocus />
          </label>
          <div className="selector__herramientas">
            <span>
              {opciones.length.toLocaleString('es-CO')} {opciones.length === 1 ? 'opción' : 'opciones'}
              {opciones.length > MAX_VISIBLES ? ` · se muestran ${MAX_VISIBLES}` : ''}
            </span>
            <span>
              {visibles.length > 0 && (
                <button type="button" className="enlace-boton" onClick={todasVisiblesMarcadas ? desmarcarVisibles : marcarVisibles}>
                  {todasVisiblesMarcadas ? 'Desmarcar visibles' : `Marcar visibles (${visibles.length})`}
                </button>
              )}
              {seleccion.length > 0 && (
                <>
                  {' · '}
                  <button type="button" className="enlace-boton" onClick={() => alCambiar([])}>
                    Limpiar
                  </button>
                </>
              )}
            </span>
          </div>
          <div className="selector__opciones" role="group" aria-label={definicion.label}>
            {visibles.map((valor) => {
              const marcada = seleccion.includes(valor);
              return (
                <label key={valor} className={`opcion ${marcada ? 'opcion--marcada' : ''}`}>
                  <input className="casilla" type="checkbox" checked={marcada} onChange={() => alternar(valor)} />
                  <span>{valor}</span>
                </label>
              );
            })}
            {!visibles.length && <p className="texto-suave chico" style={{ padding: '8px 6px' }}>No hay opciones que coincidan con «{consulta}».</p>}
          </div>
          {(definicion.truncated || opciones.length > MAX_VISIBLES) && <p className="selector__nota">La lista es amplia. Escriba parte del valor para encontrarlo más rápido.</p>}
        </div>
      )}
    </div>
  );
}
