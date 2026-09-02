import type { ModoBusqueda as Modo } from '../tipos';

export const MODOS: Array<{ id: Modo; titulo: string; detalle: string; icono: React.ReactNode }> = [
  {
    id: 'filters',
    titulo: 'Segmentar con filtros',
    detalle: 'Combine criterios',
    icono: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M2.5 4h13M5 9h8M7.5 14h3" />
      </svg>
    ),
  },
  {
    id: 'business_name',
    titulo: 'Razón social',
    detalle: 'Busque por nombre',
    icono: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="8" cy="8" r="5" />
        <path d="m12 12 3.5 3.5" />
      </svg>
    ),
  },
  {
    id: 'nit',
    titulo: 'NIT',
    detalle: 'Una empresa',
    icono: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="2.5" y="4" width="13" height="10" rx="1.5" />
        <path d="M5.5 8h3M5.5 11h5" />
      </svg>
    ),
  },
  {
    id: 'batch_nits',
    titulo: 'Lote de NIT',
    detalle: 'Archivo o lista pegada',
    icono: (
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M4 2.5h7l3 3v10H4z M11 2.5v3h3 M6.5 9h5M6.5 12h5" />
      </svg>
    ),
  },
];

export function ModoBusqueda({ modo, alCambiar }: { modo: Modo; alCambiar: (modo: Modo) => void }) {
  return (
    <div className="modo" role="group" aria-label="Formas de búsqueda">
      {MODOS.map((item) => (
        <button key={item.id} type="button" className="modo__opcion" aria-pressed={modo === item.id} onClick={() => alCambiar(item.id)}>
          <span className="modo__icono">{item.icono}</span>
          <span>
            <strong>{item.titulo}</strong>
            <small>{item.detalle}</small>
          </span>
        </button>
      ))}
    </div>
  );
}
