/**
 * Descarga del Excel formateado. Un solo paso (sin «preparar descarga»):
 * el botón pide el archivo, muestra el progreso y confirma el nombre.
 */
import { useState } from 'react';
import { descargarExcel, ErrorApi } from '../api';
import type { SolicitudBusqueda } from '../tipos';
import { IconoArchivo, Spinner } from './Interfaz';

type Props = {
  solicitud: SolicitudBusqueda;
  total: number;
  deshabilitado?: boolean;
  motivo?: string;
  unaEmpresa?: boolean;
  bloque?: boolean;
};

export function DescargaExcel({ solicitud, total, deshabilitado = false, motivo, unaEmpresa = false, bloque = false }: Props) {
  const [estado, setEstado] = useState<'inactivo' | 'preparando' | 'listo' | 'error'>('inactivo');
  const [mensaje, setMensaje] = useState('');
  const [mostrarContenido, setMostrarContenido] = useState(false);

  const descargar = async () => {
    setEstado('preparando');
    setMensaje('');
    try {
      const nombre = await descargarExcel(solicitud);
      setEstado('listo');
      setMensaje(nombre);
    } catch (error) {
      setEstado('error');
      setMensaje(error instanceof ErrorApi ? error.message : 'No fue posible preparar la descarga.');
    }
  };

  return (
    <div className={`descarga ${bloque ? 'descarga--bloque' : ''}`}>
      <button type="button" className={`boton boton--cinta descarga__boton ${bloque ? 'boton--bloque' : ''}`} onClick={descargar} disabled={deshabilitado || estado === 'preparando'} title={motivo}>
        {estado === 'preparando' ? (
          <>
            <Spinner oscuro /> Preparando Excel…
          </>
        ) : (
          <>
            <IconoArchivo tipo="XLSX" /> Descargar Excel {unaEmpresa ? 'de la empresa' : `(${total.toLocaleString('es-CO')} ${total === 1 ? 'empresa' : 'empresas'})`}
          </>
        )}
      </button>
      <p className="descarga__detalle">
        {motivo ? (
          motivo
        ) : (
          <>
            Con formato, resumen y diccionario ·{' '}
            <button type="button" className="enlace-boton" aria-expanded={mostrarContenido} onClick={() => setMostrarContenido((valor) => !valor)}>
              {mostrarContenido ? 'Ocultar contenido' : '¿Qué incluye?'}
            </button>
          </>
        )}
      </p>
      {estado === 'listo' && (
        <p className="descarga__mensaje descarga__mensaje--ok" role="status">
          <IconoArchivo tipo="XLSX" /> Archivo descargado: <span className="dato">{mensaje}</span>
        </p>
      )}
      {estado === 'error' && (
        <p className="descarga__mensaje descarga__mensaje--error" role="alert">
          {mensaje}
        </p>
      )}
      {mostrarContenido && (
        <div className="contenido-excel" style={{ alignSelf: 'stretch' }}>
          <div className="contenido-excel__cab">
            <span className="dato">XLSX</span> Un libro pensado para leerse
          </div>
          <ol>
            <li>
              <strong>Resumen</strong> Qué se consultó, con qué criterios, cuándo, cortes y fuentes.
            </li>
            {unaEmpresa && (
              <li>
                <strong>Ficha_Empresa</strong> Lectura vertical de la empresa, agrupada por secciones.
              </li>
            )}
            <li>
              <strong>Vista_Principal</strong> Variables de lectura rápida, paneles congelados y filtros.
            </li>
            <li>
              <strong>Datos_Completos</strong> Todas las variables por empresa, con anchos y formatos.
            </li>
            <li>
              <strong>Diccionario</strong> Definición, fuente y uso de cada variable.
            </li>
          </ol>
          <p>Encabezados en azul noche con acento ámbar, identificadores como texto, montos con separador de miles y valores «Sí» resaltados.</p>
        </div>
      )}
    </div>
  );
}
