import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './tipografias';
import './estilos/base.css';
import './estilos/estructura.css';
import './estilos/portada.css';
import './estilos/consulta.css';
import './estilos/resultados.css';
import './estilos/paginas.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
);
