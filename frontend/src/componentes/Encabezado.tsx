/**
 * Encabezado fijo institucional: lockup MinCIT · ProColombia, nombre del
 * aplicativo, navegación principal y menú móvil accesible (aria-expanded,
 * cierre con Escape, bloqueo de scroll, trampa de foco).
 */
import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import logoBlanco from '../assets/logos/procolombia-blanco.svg';
import { useBloquearScroll, useTrampaFoco } from '../hooks';
import { InsigniaEstado, useEstadoDatos } from './EstadoConexion';

export const RUTAS: Array<{ a: string; t: string; d: string }> = [
  { a: '/', t: 'Inicio', d: 'El aplicativo en una mirada' },
  { a: '/consultar', t: 'Consultar', d: 'Filtros, razón social, NIT y lotes' },
  { a: '/glosario', t: 'Glosario', d: 'Qué significa cada variable' },
  { a: '/metodologia', t: 'Metodología', d: 'Fuentes, cortes, alcance y límites' },
];

export function Encabezado() {
  const [abierto, setAbierto] = useState(false);
  const [conSombra, setConSombra] = useState(false);
  const botonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLElement>(null);
  const { pathname } = useLocation();
  const { estado } = useEstadoDatos();

  useEffect(() => {
    let marco = 0;
    const alDesplazar = () => {
      cancelAnimationFrame(marco);
      marco = requestAnimationFrame(() => setConSombra(window.scrollY > 8));
    };
    alDesplazar();
    window.addEventListener('scroll', alDesplazar, { passive: true });
    return () => {
      window.removeEventListener('scroll', alDesplazar);
      cancelAnimationFrame(marco);
    };
  }, []);

  useEffect(() => setAbierto(false), [pathname]);
  useBloquearScroll(abierto);
  useTrampaFoco(abierto, menuRef);

  useEffect(() => {
    if (!abierto) return;
    menuRef.current?.querySelector<HTMLElement>('a')?.focus();
    const alTeclear = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') {
        setAbierto(false);
        botonRef.current?.focus();
      }
    };
    document.addEventListener('keydown', alTeclear);
    return () => document.removeEventListener('keydown', alTeclear);
  }, [abierto]);

  return (
    <>
      <header className={`encabezado ${conSombra ? 'encabezado--sombra' : ''}`}>
        <div className="encabezado__interior">
          <Link to="/" className="encabezado__marca" aria-label="Ir al inicio · Tejido Empresarial · ProColombia">
            <img className="encabezado__logo" src={logoBlanco} alt="Ministerio de Comercio, Industria y Turismo · ProColombia" />
            <span className="encabezado__divisor" aria-hidden="true" />
            <span className="encabezado__titulo">
              <span className="encabezado__nombre">Tejido Empresarial</span>
              <p>Exportaciones · Inversión · Turismo</p>
            </span>
          </Link>

          <nav className="encabezado__nav" aria-label="Navegación principal">
            {RUTAS.map((ruta) => (
              <NavLink
                key={ruta.a}
                to={ruta.a}
                end={ruta.a === '/'}
                className={({ isActive }) => `encabezado__enlace ${isActive ? 'encabezado__enlace--activo' : ''}`}
              >
                {ruta.t}
              </NavLink>
            ))}
            <InsigniaEstado estado={estado} />
            <Link to="/consultar" className="boton boton--cinta boton--chico encabezado__cta">
              Buscar empresas
            </Link>
          </nav>

          <div className="encabezado__movil">
            <InsigniaEstado estado={estado} punto />
            <button
            ref={botonRef}
            type="button"
            className="encabezado__hamburguesa"
            aria-expanded={abierto}
            aria-controls="menu-movil"
            aria-label={abierto ? 'Cerrar el menú de navegación' : 'Abrir el menú de navegación'}
            onClick={() => setAbierto((valor) => !valor)}
          >
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            <span aria-hidden="true" />
            </button>
          </div>
        </div>
      </header>

      <nav
        ref={menuRef}
        id="menu-movil"
        className={`menu-movil ${abierto ? 'menu-movil--abierto' : ''}`}
        aria-label="Navegación principal (menú móvil)"
        aria-hidden={!abierto}
      >
        <ul className="menu-movil__lista">
          {RUTAS.map((ruta, indice) => (
            <li key={ruta.a}>
              <NavLink
                to={ruta.a}
                end={ruta.a === '/'}
                tabIndex={abierto ? 0 : -1}
                className={({ isActive }) => `menu-movil__enlace ${isActive ? 'menu-movil__enlace--activo' : ''}`}
              >
                <span className="menu-movil__numero dato" aria-hidden="true">
                  {String(indice + 1).padStart(2, '0')}
                </span>
                <span>
                  <strong>{ruta.t}</strong>
                  <span>{ruta.d}</span>
                </span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="menu-movil__estado">
          <InsigniaEstado estado={estado} />
        </div>
        <p className="menu-movil__pie">Tejido Empresarial · Gerencia de Inteligencia Comercial · ProColombia</p>
      </nav>
    </>
  );
}
