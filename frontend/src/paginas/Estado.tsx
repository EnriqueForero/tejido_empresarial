/**
 * Página «Estado del aplicativo» (/estado).
 *
 * Responde, sin tecnicismos y sin salir del navegador, tres preguntas:
 *   1. ¿Estoy viendo datos reales o de demostración?
 *   2. ¿La conexión con Snowflake funciona ahora mismo?
 *   3. Si algo falla, ¿qué hay que corregir exactamente?
 */
import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ErrorApi, obtenerDiagnostico, probarConexion } from '../api';
import { Aviso, CabeceraPagina, Spinner } from '../componentes/Interfaz';
import { TEXTOS_ESTADO, useEstadoDatos, type EstadoDatos } from '../componentes/EstadoConexion';
import { fechaHora } from '../formato';
import type { Diagnostico } from '../tipos';

const QUE_HACER: Record<Exclude<EstadoDatos, 'cargando' | 'reales'>, string[]> = {
  'sin-verificar': [
    'Espere unos segundos: la página está probando la conexión sola.',
    'Si el resultado no aparece, pulse «Probar la conexión ahora».',
  ],
  'demostración': [
    'En Railway, abra su servicio y entre a la pestaña «Variables».',
    'Borre la variable APP_DEMO_MODE (o cámbiela a false).',
    'Guarde: Railway vuelve a desplegar solo. Recargue esta página en 2 o 3 minutos.',
  ],
  'sin-conexion': [
    'En Railway, abra su servicio y entre a la pestaña «Variables».',
    'Complete las variables que aparecen más abajo como faltantes.',
    'Guarde y espere el redespliegue; luego pulse «Probar la conexión ahora».',
  ],
  problema: [
    'Pulse «Probar la conexión ahora» para confirmar si el problema sigue.',
    'Si sigue, pulse «Ver diagnóstico detallado»: indica el paso exacto que falla.',
    'Corrija lo que indique el diagnóstico en las variables de Railway y vuelva a probar.',
  ],
  desconocido: [
    'Recargue la página.',
    'Si el problema continúa, revise en Railway que el servicio esté activo (estado «Active»).',
  ],
};

function Detalle({ valor }: { valor: unknown }) {
  if (valor === null || valor === undefined) return null;
  if (typeof valor === 'string' || typeof valor === 'number') return <p className="paso-diag__texto dato">{String(valor)}</p>;
  return (
    <ul className="paso-diag__detalle">
      {Object.entries(valor as Record<string, unknown>).map(([clave, dato]) => (
        <li key={clave}>
          <span>{clave.replace(/_/g, ' ')}:</span>{' '}
          <span className="dato">{typeof dato === 'object' && dato !== null ? JSON.stringify(dato) : String(dato)}</span>
        </li>
      ))}
    </ul>
  );
}

export default function Estado() {
  const [parametros] = useSearchParams();
  const { salud, estado, consultar } = useEstadoDatos();
  const [probando, setProbando] = useState(false);
  const [resultadoPrueba, setResultadoPrueba] = useState<{ ok: boolean; mensaje: string } | null>(null);
  const [diagnostico, setDiagnostico] = useState<Diagnostico | null>(null);
  const [errorDiagnostico, setErrorDiagnostico] = useState('');
  const [cargandoDiagnostico, setCargandoDiagnostico] = useState(false);
  const [token, setToken] = useState(() => parametros.get('token') ?? '');
  const revisado = useRef(false);
  const probado = useRef(false);

  const textos = estado === 'cargando' ? null : TEXTOS_ESTADO[estado];

  const probar = useCallback(async () => {
    setProbando(true);
    setResultadoPrueba(null);
    try {
      const respuesta = await probarConexion();
      const conectado = respuesta.data_connection === 'connected';
      setResultadoPrueba({
        ok: conectado,
        mensaje: conectado
          ? 'La conexión funciona: Snowflake respondió correctamente.'
          : respuesta.data_connection === 'demo'
            ? 'El aplicativo está en modo demostración: no consulta Snowflake.'
            : 'El servicio respondió, pero no está conectado a Snowflake.',
      });
      await consultar();
    } catch (error) {
      // El servicio remite a /api/diagnostico; aquí ese diagnóstico está a un
      // botón de distancia, así que se dice en esos términos.
      const crudo = error instanceof ErrorApi ? error.message : 'No fue posible probar la conexión.';
      setResultadoPrueba({
        ok: false,
        mensaje: crudo.replace(
          /Consulte \/api\/diagnostico para ver en qué paso falla\.?/i,
          'Pulse «Ver diagnóstico detallado» para saber en qué paso falla.',
        ),
      });
      // Tras un fallo el servicio ya registró la causa: se relee para que la
      // tarjeta pase de «sin verificar» a «conexión con problemas».
      await consultar();
    } finally {
      setProbando(false);
    }
  }, [consultar]);

  // Si la configuración está completa pero nadie ha consultado todavía, la propia
  // página hace la prueba: así el visitante ve una respuesta definitiva —conectado
  // o no— sin tener que pulsar ningún botón.
  useEffect(() => {
    if (estado !== 'sin-verificar' || probado.current) return;
    probado.current = true;
    void probar();
  }, [estado, probar]);

  const revisar = useCallback(
    async (valor = token) => {
      setCargandoDiagnostico(true);
      setErrorDiagnostico('');
      try {
        setDiagnostico(await obtenerDiagnostico(valor));
      } catch (error) {
        setDiagnostico(null);
        setErrorDiagnostico(error instanceof ErrorApi ? error.message : 'No fue posible obtener el diagnóstico.');
      } finally {
        setCargandoDiagnostico(false);
      }
    },
    [token],
  );

  // Con /estado?token=… el diagnóstico se ejecuta solo: así el enlace se puede
  // guardar en favoritos y compartir con quien administre el despliegue.
  useEffect(() => {
    const desdeUrl = parametros.get('token');
    if (!desdeUrl || revisado.current) return;
    revisado.current = true;
    void revisar(desdeUrl);
  }, [parametros, revisar]);

  return (
    <>
      <CabeceraPagina
        oscura
        kicker="Estado del aplicativo"
        titulo="¿Está conectado a los datos?"
        bajada="Esta página responde en un vistazo si el aplicativo está consultando la base real de ProColombia o mostrando empresas de ejemplo, y qué hacer si algo falla."
      />
      <div className="pagina pagina--angosta estado">
        {estado === 'cargando' ? (
          <div className="estado-carga" role="status">
            <Spinner oscuro /> Consultando el estado…
          </div>
        ) : (
          <>
            <section className={`tarjeta estado-tarjeta estado-tarjeta--${estado}`} aria-live="polite">
              <span className="estado-tarjeta__punto" aria-hidden="true" />
              <div>
                <h2>{textos?.etiqueta}</h2>
                <p>{textos?.explicacion}</p>
                {estado === 'reales' && (
                  <p className="texto-suave chico mt-8">
                    Pulse «Probar la conexión ahora» si quiere confirmarlo con una consulta real a la base.
                  </p>
                )}
              </div>
            </section>

            <div className="acciones mt-16">
              <button type="button" className="boton boton--cinta" onClick={probar} disabled={probando}>
                {probando ? (
                  <>
                    <Spinner oscuro /> Probando…
                  </>
                ) : (
                  'Probar la conexión ahora'
                )}
              </button>
              <button type="button" className="boton boton--fantasma" onClick={() => void revisar()} disabled={cargandoDiagnostico}>
                {cargandoDiagnostico ? (
                  <>
                    <Spinner oscuro /> Revisando…
                  </>
                ) : (
                  'Ver diagnóstico detallado'
                )}
              </button>
              <Link className="boton boton--fantasma" to="/consultar">
                Ir a consultar empresas
              </Link>
            </div>

            {resultadoPrueba && (
              <div className="mt-16">
                <Aviso tipo={resultadoPrueba.ok ? 'ok' : 'error'}>{resultadoPrueba.mensaje}</Aviso>
              </div>
            )}

            {estado !== 'reales' && (
              <section className="tarjeta mt-20 estado-pasos" aria-labelledby="t-que-hacer">
                <h3 id="t-que-hacer">Qué hacer</h3>
                <ol>
                  {QUE_HACER[estado].map((linea) => (
                    <li key={linea}>{linea}</li>
                  ))}
                </ol>
              </section>
            )}

            {salud && (
              <section className="tarjeta mt-20" aria-labelledby="t-detalle">
                <h3 id="t-detalle">Detalle del servicio</h3>
                <dl className="estado-detalle">
                  <div>
                    <dt>Versión del aplicativo</dt>
                    <dd className="dato">{salud.version}</dd>
                  </div>
                  <div>
                    <dt>Origen configurado</dt>
                    <dd>{salud.demo_mode ? 'Demostración (empresas de ejemplo)' : 'Snowflake (base de ProColombia)'}</dd>
                  </div>
                  <div>
                    <dt>Última conexión correcta</dt>
                    <dd className="dato">
                      {salud.demo_mode
                        ? 'No aplica en modo demostración'
                        : salud.snowflake.verified_at
                          ? fechaHora(salud.snowflake.verified_at)
                          : 'Ninguna desde que arrancó el servicio'}
                    </dd>
                  </div>
                  <div>
                    <dt>Acceso</dt>
                    <dd>{salud.access_control === 'basic' ? 'Protegido con usuario y contraseña' : 'Abierto: cualquiera con el enlace entra'}</dd>
                  </div>
                  <div>
                    <dt>Conector de Snowflake</dt>
                    <dd>{salud.snowflake.connector_installed ? `Instalado (versión ${salud.snowflake.connector_version ?? '—'})` : 'No instalado'}</dd>
                  </div>
                  <div>
                    <dt>Llave configurada</dt>
                    <dd className="dato">
                      {salud.snowflake.key_sources.length
                        ? salud.snowflake.key_sources.join(', ')
                        : salud.demo_mode
                          ? 'No aplica en modo demostración'
                          : 'Ninguna'}
                    </dd>
                  </div>
                  <div>
                    <dt>Variables faltantes</dt>
                    <dd className={!salud.demo_mode && salud.snowflake.missing_variables.length ? 'dato estado-falta' : 'dato'}>
                      {salud.demo_mode
                        ? 'No aplica en modo demostración'
                        : salud.snowflake.missing_variables.length
                          ? salud.snowflake.missing_variables.join(', ')
                          : 'Ninguna'}
                    </dd>
                  </div>
                </dl>
                {salud.access_control === 'open' && (
                  <div className="mt-12">
                    <Aviso tipo="advertencia">
                      El aplicativo está abierto a cualquiera que tenga el enlace y las descargas incluyen datos de contacto de
                      empresas. Configure <strong>APP_BASIC_USER</strong> y <strong>APP_BASIC_PASSWORD</strong> en Railway para
                      pedir usuario y contraseña.
                    </Aviso>
                  </div>
                )}
              </section>
            )}

            {errorDiagnostico && (
              <section className="tarjeta mt-20" aria-labelledby="t-diag-error">
                <h3 id="t-diag-error">Diagnóstico detallado</h3>
                <div className="mt-12">
                  <Aviso tipo="advertencia">{errorDiagnostico}</Aviso>
                </div>
                <p className="texto-suave chico mt-12">
                  Si en Railway configuró <strong>APP_DIAG_TOKEN</strong>, escriba aquí ese valor y vuelva a intentarlo.
                </p>
                <div className="estado-token mt-8">
                  <input
                    className="campo"
                    value={token}
                    onChange={(evento) => setToken(evento.target.value)}
                    placeholder="Valor de APP_DIAG_TOKEN"
                    aria-label="Valor de APP_DIAG_TOKEN"
                  />
                  <button type="button" className="boton boton--primario" onClick={() => void revisar()} disabled={!token || cargandoDiagnostico}>
                    Reintentar
                  </button>
                </div>
              </section>
            )}

            {diagnostico && (
              <section className="tarjeta mt-20" aria-labelledby="t-diagnostico">
                <h3 id="t-diagnostico">Diagnóstico detallado</h3>
                <div className="mt-12">
                  <Aviso tipo={diagnostico.todo_ok === false ? 'error' : 'ok'}>{diagnostico.resumen}</Aviso>
                </div>
                {diagnostico.siguiente_paso && (
                  <p className="estado-sugerencia">
                    <strong>Qué hacer:</strong> {diagnostico.siguiente_paso}
                  </p>
                )}
                {diagnostico.pasos.length > 0 && (
                  <ol className="pasos-diag">
                    {diagnostico.pasos.map((paso) => (
                      <li key={paso.paso} className={paso.ok ? 'paso-diag paso-diag--ok' : 'paso-diag paso-diag--falla'}>
                        <span className="paso-diag__marca" aria-hidden="true">
                          {paso.ok ? '✓' : '✗'}
                        </span>
                        <div>
                          <strong>{paso.descripcion}</strong>
                          <span className="paso-diag__tiempo dato">{paso.segundos}s</span>
                          {paso.ok ? <Detalle valor={paso.detalle} /> : <p className="paso-diag__error">{paso.error}</p>}
                        </div>
                      </li>
                    ))}
                  </ol>
                )}
              </section>
            )}
          </>
        )}
      </div>
    </>
  );
}
