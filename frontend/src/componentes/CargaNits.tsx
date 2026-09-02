/**
 * Búsqueda masiva por NIT: archivo .txt/.csv arrastrado o seleccionado, o
 * lista pegada directamente. Limpia, valida (2 a 12 dígitos) y deduplica.
 */
import { useRef, useState } from 'react';
import { IconoArchivo, Spinner } from './Interfaz';

type Props = {
  nits: string[];
  maximo: number;
  alCambiar: (nits: string[], origen: string) => void;
  alConsultar: () => void;
  cargando: boolean;
};

export function extraerNits(texto: string, maximo: number): { validos: string[]; descartados: number } {
  const lineas = texto
    .split(/[\r\n;,\t ]+/)
    .map((linea) => linea.trim())
    .filter(Boolean);
  const vistos = new Set<string>();
  let descartados = 0;
  for (const linea of lineas) {
    const digitos = linea.replace(/[.\-\s]/g, '');
    // Se acepta NIT con o sin dígito de verificación separado por guion; se conserva sólo la parte principal.
    const principal = linea.includes('-') ? linea.split('-')[0].replace(/\D/g, '') : digitos.replace(/\D/g, '');
    if (principal.length >= 2 && principal.length <= 12 && /^\d+$/.test(principal)) vistos.add(principal);
    else descartados += 1;
    if (vistos.size >= maximo) break;
  }
  return { validos: [...vistos], descartados };
}

export function CargaNits({ nits, maximo, alCambiar, alConsultar, cargando }: Props) {
  const [arrastrando, setArrastrando] = useState(false);
  const [nombre, setNombre] = useState('');
  const [texto, setTexto] = useState('');
  const [descartados, setDescartados] = useState(0);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const procesar = (contenido: string, origen: string) => {
    const { validos, descartados: fuera } = extraerNits(contenido, maximo);
    setDescartados(fuera);
    setError(validos.length ? '' : 'No encontramos NIT válidos. Use un número por línea, entre 2 y 12 dígitos.');
    alCambiar(validos, origen);
  };

  const leerArchivo = async (archivo: File | undefined) => {
    if (!archivo) return;
    if (archivo.size > 1_000_000) {
      setError('El archivo supera 1 MB. Divida la consulta en lotes más pequeños.');
      return;
    }
    const contenido = await archivo.text();
    setNombre(archivo.name);
    setTexto('');
    procesar(contenido, archivo.name);
  };

  return (
    <div className="lote">
      <label
        className={`zona-carga ${arrastrando ? 'zona-carga--activa' : ''}`}
        onDragOver={(evento) => {
          evento.preventDefault();
          setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(evento) => {
          evento.preventDefault();
          setArrastrando(false);
          void leerArchivo(evento.dataTransfer.files?.[0]);
        }}
      >
        <input ref={inputRef} type="file" accept=".txt,.csv,text/plain,text/csv" onChange={(evento) => void leerArchivo(evento.target.files?.[0])} aria-label="Seleccionar archivo con NIT" />
        <span className="zona-carga__icono">
          <IconoArchivo tipo="TXT" />
        </span>
        <strong>{nombre || 'Arrastre aquí un archivo .txt o haga clic para elegirlo'}</strong>
        <span>Un NIT por línea · máximo {maximo.toLocaleString('es-CO')} NIT · 1 MB</span>
      </label>
      <p className="lote__o">o pegue la lista</p>
      <textarea
        className="campo"
        value={texto}
        placeholder={'901067966\n760459043\n890905456'}
        aria-label="Pegue los NIT, uno por línea"
        onChange={(evento) => {
          setTexto(evento.target.value);
          setNombre('');
          if (evento.target.value.trim()) procesar(evento.target.value, 'lista pegada');
          else {
            setDescartados(0);
            setError('');
            alCambiar([], '');
          }
        }}
      />
      {error && (
        <div className="aviso aviso--advertencia" role="alert">
          {error}
        </div>
      )}
      {nits.length > 0 && (
        <div className="lote__resumen">
          <div>
            <strong className="dato">{nits.length.toLocaleString('es-CO')}</strong>
            <small>
              NIT únicos y válidos
              {descartados > 0 ? ` · ${descartados} ${descartados === 1 ? 'línea descartada' : 'líneas descartadas'}` : ''}
            </small>
          </div>
          <div className="lote__vista" aria-label="Vista previa de NIT">
            {nits.slice(0, 18).map((nit) => (
              <span key={nit}>{nit}</span>
            ))}
            {nits.length > 18 && <span>+{(nits.length - 18).toLocaleString('es-CO')}</span>}
          </div>
          <button type="button" className="boton boton--cinta" onClick={alConsultar} disabled={cargando}>
            {cargando ? (
              <>
                <Spinner oscuro /> Consultando…
              </>
            ) : (
              <>
                Consultar lote <span className="boton__flecha" aria-hidden="true">→</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
