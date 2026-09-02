import type { DefinicionFiltro, Diagnostico, Ficha, Metadatos, RespuestaBusqueda, RespuestaGlosario, Salud, SolicitudBusqueda } from './tipos';

type CuerpoError = { detail?: string | Array<{ msg?: string }> };

export class ErrorApi extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ErrorApi';
    this.status = status;
  }
}

function mensajeDe(body: CuerpoError, porDefecto: string): string {
  if (typeof body.detail === 'string') return body.detail;
  if (Array.isArray(body.detail)) {
    const primero = body.detail[0]?.msg;
    if (primero) return primero.replace(/^Value error,\s*/i, '');
  }
  return porDefecto;
}

async function leerError(response: Response, porDefecto: string): Promise<ErrorApi> {
  let body: CuerpoError = {};
  try {
    body = (await response.json()) as CuerpoError;
  } catch {
    /* respuesta sin JSON */
  }
  if (response.status === 401) return new ErrorApi('Esta instancia requiere usuario y contraseña. Recargue la página e ingrese sus credenciales.', 401);
  if (response.status === 503) return new ErrorApi(mensajeDe(body, 'El servicio de datos no está disponible en este momento.'), 503);
  return new ErrorApi(mensajeDe(body, porDefecto), response.status);
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) } });
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') throw error;
    throw new ErrorApi('No hay conexión con el servidor. Verifique su red e intente de nuevo.', 0);
  }
  if (!response.ok) throw await leerError(response, 'No fue posible completar la solicitud.');
  return (await response.json()) as T;
}

export const obtenerMetadatos = () => json<Metadatos>('/api/metadata');
export const obtenerSalud = () => json<Salud>('/api/health');
/** Prueba real contra Snowflake: puede tardar unos segundos. */
export const probarConexion = () => json<Salud>('/api/health?deep=true');
export const obtenerDiagnostico = (token = '') =>
  json<Diagnostico>(`/api/diagnostico${token ? `?token=${encodeURIComponent(token)}` : ''}`);
export const obtenerGlosario = () => json<RespuestaGlosario>('/api/glossary');
export const obtenerFicha = (nit: string, signal?: AbortSignal) => json<Ficha>(`/api/companies/${encodeURIComponent(nit)}`, { signal });

export function obtenerOpcionesFiltros(selections: Record<string, string[]>, signal?: AbortSignal) {
  return json<{ filters: DefinicionFiltro[]; demo: boolean }>('/api/filters/options', {
    method: 'POST',
    body: JSON.stringify({ selections }),
    signal,
  });
}

export function buscarEmpresas(solicitud: SolicitudBusqueda, signal?: AbortSignal) {
  return json<RespuestaBusqueda>('/api/companies/search', { method: 'POST', body: JSON.stringify(solicitud), signal });
}

/** Descarga el Excel y lo entrega al navegador. Devuelve el nombre del archivo. */
export async function descargarExcel(solicitud: SolicitudBusqueda): Promise<string> {
  let response: Response;
  try {
    response = await fetch('/api/companies/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...solicitud, page: 1 }),
    });
  } catch {
    throw new ErrorApi('No hay conexión con el servidor. Verifique su red e intente de nuevo.', 0);
  }
  if (!response.ok) throw await leerError(response, 'No fue posible preparar el archivo.');
  const blob = await response.blob();
  const codificado = response.headers.get('X-Export-Filename');
  const nombre = codificado ? decodeURIComponent(codificado) : 'ProColombia_TejidoEmpresarial.xlsx';
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement('a');
  enlace.href = url;
  enlace.download = nombre;
  enlace.rel = 'noopener';
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 4000);
  return nombre;
}
