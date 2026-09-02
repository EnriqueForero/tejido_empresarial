/**
 * Pie institucional. Conserva los bloques del aplicativo original
 * (líneas de atención, ejes de ProColombia, enlaces de interés) con la
 * identidad visual de la familia digital ProColombia.
 */
import { Link } from 'react-router-dom';
import logoBlanco from '../assets/logos/procolombia-blanco.svg';
import { RUTAS } from './Encabezado';

const EJES = [
  { t: 'ProColombia', u: 'https://procolombia.co/' },
  { t: 'Exportaciones', u: 'https://procolombia.co/colombiatrade' },
  { t: 'Inversión', u: 'https://investincolombia.com.co/es' },
  { t: 'Turismo', u: 'https://colombia.travel/es' },
  { t: 'Marca País', u: 'https://colombia.co/' },
];

const ENLACES = [
  { t: 'Servicios al ciudadano', u: 'https://procolombia.co/transparencia/glosario' },
  { t: 'Informe de sostenibilidad', u: 'https://procolombia.co/sostenibilidad' },
  { t: 'Preguntas frecuentes', u: 'https://procolombia.co/transparencia/preguntas-frecuentes' },
  { t: 'PQRFS', u: 'https://procolombia.co/transparencia/pqrfs' },
  { t: 'Contacto', u: 'https://procolombia.co/contacto' },
];

export function Pie() {
  return (
    <footer className="pie">
      <div className="pie__interior">
        <div className="pie__columna pie__columna--marca">
          <img className="pie__lockup" src={logoBlanco} alt="Ministerio de Comercio, Industria y Turismo · ProColombia" />
          <p className="pie__aviso">
            <strong>Tejido Empresarial</strong> es la herramienta de la Gerencia de Inteligencia Comercial de ProColombia para
            identificar, segmentar y priorizar empresas colombianas en apoyo a los ejes de Exportaciones, Inversión y Turismo.
            La información es cuantitativa y de uso institucional; la segmentación final combina estos datos con el criterio de los
            equipos.
          </p>
          <p className="pie__fuentes">
            Fuentes: RUES, Supersociedades, DANE–DIAN y CRM ProColombia. Las cifras de exportación de servicios provienen de los
            negocios reportados a ProColombia y no representan el total nacional.
          </p>
        </div>
        <div className="pie__columna">
          <h3>Líneas de atención</h3>
          <ul className="pie__lista">
            <li>Calle 28 No. 13A - 15, pisos 35-36</li>
            <li>Bogotá, Colombia</li>
            <li>+57 601 5600100</li>
            <li>Fax +57 601 5600104</li>
            <li>Lunes a viernes, 8:30 a. m. – 5:30 p. m.</li>
          </ul>
        </div>
        <div className="pie__columna">
          <h3>Nuestros ejes</h3>
          <nav className="pie__nav" aria-label="Ejes de ProColombia">
            {EJES.map((eje) => (
              <a key={eje.u} href={eje.u} target="_blank" rel="noopener noreferrer">
                {eje.t}
              </a>
            ))}
          </nav>
        </div>
        <div className="pie__columna">
          <h3>Enlaces de interés</h3>
          <nav className="pie__nav" aria-label="Enlaces de interés">
            {ENLACES.map((enlace) => (
              <a key={enlace.u} href={enlace.u} target="_blank" rel="noopener noreferrer">
                {enlace.t}
              </a>
            ))}
          </nav>
          <h3 className="mt-20">Aplicativo</h3>
          <nav className="pie__nav" aria-label="Mapa del aplicativo">
            {RUTAS.map((ruta) => (
              <Link key={ruta.a} to={ruta.a}>
                {ruta.t}
              </Link>
            ))}
            <Link to="/estado">Estado del aplicativo</Link>
          </nav>
        </div>
      </div>
      <div className="pie__legal">
        <p className="dato">Tejido Empresarial · Gerencia de Inteligencia Comercial · ProColombia · 2026</p>
        <p className="dato">RUES corte 30-jun-2026 · Exportaciones 2021 – ene-may 2026 · Glosario 01-sep-2026</p>
      </div>
    </footer>
  );
}
