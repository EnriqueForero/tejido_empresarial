/**
 * Estado de la conexión de datos, en lenguaje claro.
 *
 * `useEstadoDatos` consulta /api/health (rápido, no toca Snowflake) y traduce la
 * respuesta a estados que cualquier persona puede interpretar:
 *
 *   reales         · ya hubo una consulta correcta a la base de ProColombia
 *   sin-verificar  · la configuración está completa, pero aún no se ha probado
 *   demostración   · muestra empresas de ejemplo, no reales
 *   problema       · hay configuración, pero la conexión falló
 *   sin-conexion   · falta configuración en el servidor
 *
 * La diferencia entre «reales» y «sin-verificar» es deliberada: el aplicativo no
 * afirma que está conectado hasta que Snowflake haya respondido de verdad. La
 * página /estado hace esa prueba sola al abrirse.
 */
import { useCallback, useEffect, useSyncExternalStore } from 'react';
import { Link } from 'react-router-dom';
import { obtenerSalud } from '../api';
import type { Salud } from '../tipos';

export type EstadoDatos =
  | 'cargando'
  | 'reales'
  | 'sin-verificar'
  | 'demostración'
  | 'problema'
  | 'sin-conexion'
  | 'desconocido';

export const TEXTOS_ESTADO: Record<Exclude<EstadoDatos, 'cargando'>, { etiqueta: string; explicacion: string }> = {
  reales: {
    etiqueta: 'Datos reales',
    explicacion: 'El aplicativo está conectado a la base de datos de ProColombia en Snowflake.',
  },
  'sin-verificar': {
    etiqueta: 'Sin verificar',
    explicacion:
      'La configuración de Snowflake está completa, pero todavía no se ha hecho ninguna consulta. Pulse «Probar la conexión ahora» para confirmarlo.',
  },
  demostración: {
    etiqueta: 'Modo demostración',
    explicacion: 'Las empresas que ve son de ejemplo, no son reales. Sirve para revisar el diseño y la navegación.',
  },
  problema: {
    etiqueta: 'Conexión con problemas',
    explicacion: 'La configuración está completa, pero la última consulta a Snowflake falló.',
  },
  'sin-conexion': {
    etiqueta: 'Sin conexión a datos',
    explicacion: 'Falta configuración en el servidor: el aplicativo no puede consultar Snowflake.',
  },
  desconocido: {
    etiqueta: 'Estado desconocido',
    explicacion: 'No fue posible consultar el estado del servicio.',
  },
};

export function clasificar(salud: Salud | null): EstadoDatos {
  if (!salud) return 'desconocido';
  if (salud.data_connection === 'demo') return 'demostración';
  if (salud.data_connection === 'missing_configuration') return 'sin-conexion';
  if (salud.data_connection === 'error' || salud.snowflake?.connection_error) return 'problema';
  if (salud.data_connection === 'connected') return 'reales';
  return 'sin-verificar';
}

/**
 * Estado compartido por toda la aplicación.
 *
 * El encabezado y la página /estado leen lo mismo: así la pastilla se actualiza
 * cuando la página prueba la conexión, y no se pide /api/health por duplicado.
 */
type Instantanea = { salud: Salud | null; estado: EstadoDatos };

let instantanea: Instantanea = { salud: null, estado: 'cargando' };
const suscriptores = new Set<() => void>();
let enVuelo: Promise<void> | null = null;

function publicar(siguiente: Instantanea) {
  instantanea = siguiente;
  suscriptores.forEach((avisar) => avisar());
}

async function refrescar(): Promise<void> {
  if (enVuelo) return enVuelo;
  enVuelo = (async () => {
    try {
      const respuesta = await obtenerSalud();
      publicar({ salud: respuesta, estado: clasificar(respuesta) });
    } catch {
      publicar({ salud: null, estado: 'desconocido' });
    } finally {
      enVuelo = null;
    }
  })();
  return enVuelo;
}

function suscribir(avisar: () => void) {
  suscriptores.add(avisar);
  return () => {
    suscriptores.delete(avisar);
  };
}

const leer = () => instantanea;

export function useEstadoDatos() {
  // useSyncExternalStore garantiza que encabezado y página lean la misma
  // instantánea aunque React renderice de forma concurrente o la página llegue
  // por carga diferida: sin él una de las dos se quedaba con el valor inicial.
  const { salud, estado } = useSyncExternalStore(suscribir, leer, leer);

  useEffect(() => {
    if (estado === 'cargando') void refrescar();
  }, [estado]);

  const consultar = useCallback(() => refrescar(), []);
  return { salud, estado, consultar };
}

/**
 * Pastilla que enlaza a la página de estado.
 *
 * `punto` deja sólo el círculo de color: es la variante del encabezado móvil,
 * donde no cabe el texto pero sí conviene ver de un vistazo si algo va mal.
 */
export function InsigniaEstado({
  estado,
  compacta = false,
  punto = false,
}: {
  estado: EstadoDatos;
  compacta?: boolean;
  punto?: boolean;
}) {
  if (estado === 'cargando') return null;
  const { etiqueta } = TEXTOS_ESTADO[estado];
  const clases = ['insignia', `insignia--${estado}`];
  if (compacta) clases.push('insignia--compacta');
  if (punto) clases.push('insignia--punto');
  return (
    <Link to="/estado" className={clases.join(' ')} title={`Estado del aplicativo: ${etiqueta}`} aria-label={`Estado del aplicativo: ${etiqueta}`}>
      <span className="insignia__punto" aria-hidden="true" />
      {punto ? null : etiqueta}
    </Link>
  );
}
