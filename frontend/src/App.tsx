import { Suspense, lazy, useEffect } from 'react';
import { Route, Routes, useLocation } from 'react-router-dom';
import { Encabezado } from './componentes/Encabezado';
import { Pie } from './componentes/Pie';
import { BotonArriba } from './componentes/Interfaz';
import Inicio from './paginas/Inicio';

const Consultar = lazy(() => import('./paginas/Consultar'));
const Glosario = lazy(() => import('./paginas/Glosario'));
const Metodologia = lazy(() => import('./paginas/Metodologia'));
const FichaEmpresa = lazy(() => import('./paginas/FichaEmpresa'));
const Estado = lazy(() => import('./paginas/Estado'));

const TITULOS: Record<string, string> = {
  '/': 'Inicio',
  '/consultar': 'Consultar empresas',
  '/glosario': 'Glosario de variables',
  '/metodologia': 'Metodología y alcance',
  '/estado': 'Estado del aplicativo',
};

/** Al cambiar de página: título del documento, scroll arriba y foco en el contenido. */
function ControlDePagina() {
  const { pathname } = useLocation();
  useEffect(() => {
    const titulo = pathname.startsWith('/empresa/') ? 'Ficha de empresa' : TITULOS[pathname] ?? 'Inicio';
    document.title = `${titulo} · Tejido Empresarial · ProColombia`;
    window.scrollTo({ top: 0, behavior: 'auto' });
    window.requestAnimationFrame(() => document.getElementById('contenido-principal')?.focus({ preventScroll: true }));
  }, [pathname]);
  return null;
}

export default function App() {
  const { pathname } = useLocation();
  return (
    <>
      <ControlDePagina />
      <a
        className="saltar-contenido"
        href="#contenido-principal"
        onClick={(evento) => {
          evento.preventDefault();
          document.getElementById('contenido-principal')?.focus();
        }}
      >
        Saltar al contenido principal
      </a>
      <Encabezado />
      <main id="contenido-principal" tabIndex={-1}>
        <Suspense
          fallback={
            <div className="pagina estado-carga" role="status">
              <span className="spinner spinner--oscuro" aria-hidden="true" /> Cargando…
            </div>
          }
        >
          <div key={pathname} className="transicion-pagina">
            <Routes>
              <Route path="/" element={<Inicio />} />
              <Route path="/consultar" element={<Consultar />} />
              <Route path="/glosario" element={<Glosario />} />
              <Route path="/metodologia" element={<Metodologia />} />
              <Route path="/empresa/:nit" element={<FichaEmpresa />} />
              <Route path="/estado" element={<Estado />} />
              <Route path="*" element={<Inicio />} />
            </Routes>
          </div>
        </Suspense>
      </main>
      <BotonArriba />
      <Pie />
    </>
  );
}
