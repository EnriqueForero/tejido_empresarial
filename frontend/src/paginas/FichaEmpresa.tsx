/**
 * Ficha completa de una empresa (/empresa/:nit): cabecera, indicadores,
 * exportaciones por periodo y todas las variables agrupadas por secciones.
 */
import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ErrorApi, obtenerFicha } from '../api';
import { DescargaExcel } from '../componentes/DescargaExcel';
import { Aviso, CabeceraPagina, EstadoVacio, Pastilla, Spinner } from '../componentes/Interfaz';
import { abreviar, esNumericaVisual, formatearCompacto, formatearValor } from '../formato';
import type { Ficha } from '../tipos';

const EXPO_PREFIJO = 'Exportaciones totales de la empresa ';

function GraficoExportaciones({ campos }: { campos: Array<{ name: string; value: string | number | null }> }) {
  const series = campos
    .filter((campo) => campo.name.startsWith(EXPO_PREFIJO))
    .map((campo) => {
      const etiqueta = campo.name.replace(EXPO_PREFIJO, '').replace(' (FOB USD)', '');
      const corrido = /enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre/i.test(etiqueta);
      const corta = corrido ? etiqueta.replace(/^(\w{3})\w*\s*-\s*(\w{3})\w*\s*(\d{4})$/i, '$1-$2 $3') : etiqueta;
      return { etiqueta, corta, corrido, valor: typeof campo.value === 'number' ? campo.value : 0 };
    });
  if (!series.length) return null;
  const maximo = Math.max(...series.map((s) => s.valor), 1);
  const ancho = 460;
  const alto = 170;
  const margen = { izq: 8, der: 8, sup: 18, inf: 36 };
  const anchoBarra = (ancho - margen.izq - margen.der) / series.length;
  const sinDatos = series.every((s) => s.valor === 0);
  return (
    <div className="tarjeta grafico-expo">
      <h3>Exportaciones por periodo</h3>
      <p>{sinDatos ? 'La empresa no registra exportaciones de bienes en el periodo disponible.' : 'FOB USD · años cerrados y periodo corrido'}</p>
      <svg viewBox={`0 0 ${ancho} ${alto}`} role="img" aria-label={`Exportaciones por periodo: ${series.map((s) => `${s.etiqueta} ${formatearValor(s.valor, 'FOB USD')}`).join(', ')}`}>
        <line x1={margen.izq} x2={ancho - margen.der} y1={alto - margen.inf} y2={alto - margen.inf} stroke="#d5dee5" />
        {series.map((s, i) => {
          const h = sinDatos ? 0 : Math.max(2, ((alto - margen.inf - margen.sup) * s.valor) / maximo);
          const x = margen.izq + i * anchoBarra + anchoBarra * 0.15;
          const y = alto - margen.inf - h;
          return (
            <g key={s.etiqueta}>
              <rect className={`barra barra--anim ${s.corrido ? 'barra--corrido' : ''}`} x={x} y={y} width={anchoBarra * 0.7} height={h} rx="3" style={{ animationDelay: `${i * 60}ms` }} />
              {s.valor > 0 && (
                <text x={x + anchoBarra * 0.35} y={y - 5} textAnchor="middle">
                  {abreviar(s.valor)}
                </text>
              )}
              <text x={x + anchoBarra * 0.35} y={alto - margen.inf + 14} textAnchor="middle">
                {s.corta.split(' ')[0]}
              </text>
              {s.corrido && (
                <text x={x + anchoBarra * 0.35} y={alto - margen.inf + 26} textAnchor="middle">
                  {s.corta.split(' ')[1] ?? ''}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <div className="grafico-expo__leyenda">
        <span>
          <i /> Año cerrado
        </span>
        <span>
          <i className="corrido" /> Periodo corrido
        </span>
      </div>
    </div>
  );
}

export default function FichaEmpresa() {
  const { nit = '' } = useParams();
  const navegar = useNavigate();
  const [ficha, setFicha] = useState<Ficha | null>(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    const controlador = new AbortController();
    setCargando(true);
    setError('');
    setFicha(null);
    obtenerFicha(nit, controlador.signal)
      .then(setFicha)
      .catch((razon: unknown) => {
        if (razon instanceof DOMException && razon.name === 'AbortError') return;
        setError(razon instanceof ErrorApi ? razon.message : 'No fue posible consultar la ficha.');
      })
      .finally(() => setCargando(false));
    return () => controlador.abort();
  }, [nit]);

  const registro = ficha?.record;
  const kpis = useMemo(() => {
    if (!registro) return [];
    const expo = Object.keys(registro).filter((k) => k.startsWith(EXPO_PREFIJO));
    const ultimaCerrada = expo.filter((k) => !/enero/i.test(k)).at(-1);
    const corrido = expo.at(-1);
    return [
      { etiqueta: 'Ingresos operacionales', valor: formatearCompacto(registro['Ingresos operacionales (COP)'], 'Ingresos operacionales (COP)'), detalle: registro['Rango de ingresos operacionales (COP)'] },
      { etiqueta: 'Empleados', valor: formatearValor(registro.Empleados, 'Empleados'), detalle: registro['Cantidad de mujeres empleadas'] != null ? `${formatearValor(registro['Cantidad de mujeres empleadas'], 'Cantidad')} mujeres` : null },
      { etiqueta: ultimaCerrada ? `Exportaciones ${ultimaCerrada.replace(EXPO_PREFIJO, '').replace(' (FOB USD)', '')}` : 'Exportaciones', valor: ultimaCerrada ? formatearCompacto(registro[ultimaCerrada], 'FOB USD') : '—', detalle: registro['Trayectoria exportadora'] },
      { etiqueta: corrido ? `Exportaciones ${corrido.replace(EXPO_PREFIJO, '').replace(' (FOB USD)', '')}` : 'Periodo corrido', valor: corrido ? formatearCompacto(registro[corrido], 'FOB USD') : '—', detalle: registro['País destino estrella'] ? `Destino estrella: ${registro['País destino estrella']}` : null },
    ];
  }, [registro]);

  return (
    <>
      <CabeceraPagina
        oscura
        kicker="Ficha de empresa"
        titulo={registro ? String(registro['Razón social'] ?? 'Empresa') : cargando ? 'Consultando…' : 'Ficha no disponible'}
        bajada={
          registro ? (
            <div className="ficha-cab__nit">
              <span className="etiqueta-mini etiqueta-mini--acento dato">NIT {ficha?.nit}</span>
              {registro['Dígito de verificación'] != null && <span className="etiqueta-mini etiqueta-mini--acento dato">DV {String(registro['Dígito de verificación'])}</span>}
              {registro['Tamaño de la empresa'] && <span className="etiqueta-mini etiqueta-mini--azul">{String(registro['Tamaño de la empresa'])}</span>}
              {registro['Municipio de la empresa'] && (
                <span className="etiqueta-mini">
                  {String(registro['Municipio de la empresa'])}, {String(registro['Departamento de la empresa'] ?? '')}
                </span>
              )}
              {registro['Cadena de segmentación'] && <span className="etiqueta-mini">{String(registro['Cadena de segmentación'])}</span>}
              {registro['¿La empresa ha exportado?'] === 'Sí' && <Pastilla tono="ok">Ha exportado</Pastilla>}
            </div>
          ) : undefined
        }
        lateral={
          <button type="button" className="boton boton--vidrio" onClick={() => (window.history.length > 1 ? navegar(-1) : navegar('/consultar'))}>
            ← Volver a los resultados
          </button>
        }
      />
      <div className="pagina">
        {cargando && (
          <div className="estado-carga" role="status">
            <Spinner oscuro /> Consultando la ficha…
          </div>
        )}
        {error && (
          <>
            <Aviso tipo="error">{error}</Aviso>
            <EstadoVacio titulo="No fue posible mostrar la ficha" texto="Verifique el NIT o vuelva a la consulta.">
              <Link className="boton boton--fantasma mt-12" to="/consultar?modo=nit">
                Buscar por NIT
              </Link>
            </EstadoVacio>
          </>
        )}
        {ficha && registro && (
          <>
            {ficha.demo && <Aviso tipo="info">Modo de demostración: esta empresa es sintética.</Aviso>}
            {ficha.matches > 1 && <Aviso tipo="advertencia">La base contiene {ficha.matches} registros con este NIT (por ejemplo, distintas sedes). Se muestra el de mayores ingresos; la descarga incluye todos.</Aviso>}
            <div className="ficha-kpis">
              {kpis.map((kpi) => (
                <div key={kpi.etiqueta} className="tarjeta kpi">
                  <p className="kpi__etiqueta">{kpi.etiqueta}</p>
                  <p className="kpi__valor">{kpi.valor}</p>
                  {kpi.detalle && <p className="kpi__detalle">{String(kpi.detalle)}</p>}
                </div>
              ))}
            </div>
            <div className="ficha-cuerpo">
              <div className="ficha-secciones">
                {ficha.sections.map((seccion) => (
                  <section key={seccion.title} className="tarjeta seccion-ficha" aria-label={seccion.title}>
                    <h3>{seccion.title}</h3>
                    <dl>
                      {seccion.fields.map((campo) => {
                        const vacio = campo.value === null || campo.value === undefined || campo.value === '';
                        return (
                          <div key={campo.name}>
                            <dt>{campo.name}</dt>
                            <dd className={`${esNumericaVisual(campo.name, campo.value) || campo.name === 'NIT' || campo.name.startsWith('Código') ? 'dato' : ''} ${vacio ? 'vacio' : ''}`.trim()}>{vacio ? 'Sin dato' : formatearValor(campo.value, campo.name)}</dd>
                          </div>
                        );
                      })}
                    </dl>
                  </section>
                ))}
              </div>
              <aside className="ficha-lateral">
                <GraficoExportaciones campos={ficha.sections.flatMap((s) => s.fields)} />
                <div className="tarjeta ficha-acciones">
                  <DescargaExcel solicitud={{ mode: 'nit', filters: {}, term: ficha.nit, nits: [], page: 1, page_size: 25 }} total={ficha.matches} unaEmpresa bloque />
                  <p>El Excel de una empresa incluye la hoja «Ficha_Empresa» con lectura vertical por secciones, además del resumen y el diccionario.</p>
                  <Link to="/glosario" className="boton boton--fantasma boton--chico">
                    ¿Qué significa cada variable?
                  </Link>
                </div>
              </aside>
            </div>
          </>
        )}
      </div>
    </>
  );
}
