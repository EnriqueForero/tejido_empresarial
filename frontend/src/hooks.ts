import { useEffect, useRef, useState } from 'react';

export function prefiereMenosMovimiento(): boolean {
  return typeof window !== 'undefined' && typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** true cuando la consulta de medios coincide (se actualiza en vivo). */
export function useMediaQuery(consulta: string): boolean {
  const [coincide, setCoincide] = useState(() => typeof window !== 'undefined' && window.matchMedia(consulta).matches);
  useEffect(() => {
    const media = window.matchMedia(consulta);
    const alCambiar = (evento: MediaQueryListEvent) => setCoincide(evento.matches);
    setCoincide(media.matches);
    media.addEventListener('change', alCambiar);
    return () => media.removeEventListener('change', alCambiar);
  }, [consulta]);
  return coincide;
}

/** Retrasa la propagación de un valor que cambia rápido (búsquedas locales). */
export function useDebounce<T>(valor: T, retraso = 200): T {
  const [retrasado, setRetrasado] = useState(valor);
  useEffect(() => {
    const temporizador = window.setTimeout(() => setRetrasado(valor), retraso);
    return () => window.clearTimeout(temporizador);
  }, [valor, retraso]);
  return retrasado;
}

/** Marca el elemento la primera vez que entra en pantalla (revelado al hacer scroll). */
export function useVisible<T extends HTMLElement>(margen = '0px 0px -8% 0px') {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const nodo = ref.current;
    if (!nodo) return;
    if (prefiereMenosMovimiento() || typeof IntersectionObserver === 'undefined') {
      setVisible(true);
      return;
    }
    const observador = new IntersectionObserver(
      (entradas) => {
        if (entradas.some((entrada) => entrada.isIntersecting)) {
          setVisible(true);
          observador.disconnect();
        }
      },
      { rootMargin: margen, threshold: 0.08 },
    );
    observador.observe(nodo);
    // Respaldo: si el observador no llega a disparar (navegadores o contextos atípicos), se muestra igual.
    const respaldo = window.setTimeout(() => setVisible(true), 1800);
    return () => {
      observador.disconnect();
      window.clearTimeout(respaldo);
    };
  }, [margen]);
  return { ref, visible };
}

/** Cierra al hacer clic fuera o con Escape. */
export function useCerrarAlExterior(activo: boolean, ref: React.RefObject<HTMLElement | null>, cerrar: () => void) {
  useEffect(() => {
    if (!activo) return;
    const alClic = (evento: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(evento.target as Node)) cerrar();
    };
    const alTeclear = (evento: KeyboardEvent) => {
      if (evento.key === 'Escape') cerrar();
    };
    document.addEventListener('mousedown', alClic);
    document.addEventListener('touchstart', alClic, { passive: true });
    document.addEventListener('keydown', alTeclear);
    return () => {
      document.removeEventListener('mousedown', alClic);
      document.removeEventListener('touchstart', alClic);
      document.removeEventListener('keydown', alTeclear);
    };
  }, [activo, ref, cerrar]);
}

/** Bloquea el scroll del cuerpo mientras un panel modal está abierto. */
export function useBloquearScroll(activo: boolean) {
  useEffect(() => {
    document.body.classList.toggle('sin-scroll', activo);
    return () => document.body.classList.remove('sin-scroll');
  }, [activo]);
}

/** Atrapa el foco dentro de un contenedor (menús y cajones modales). */
export function useTrampaFoco(activo: boolean, ref: React.RefObject<HTMLElement | null>) {
  useEffect(() => {
    if (!activo) return;
    const alTeclear = (evento: KeyboardEvent) => {
      if (evento.key !== 'Tab' || !ref.current) return;
      const enfocables = [...ref.current.querySelectorAll<HTMLElement>('a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])')].filter(
        (elemento) => elemento.offsetParent !== null,
      );
      if (!enfocables.length) return;
      const primero = enfocables[0];
      const ultimo = enfocables[enfocables.length - 1];
      if (evento.shiftKey && document.activeElement === primero) {
        evento.preventDefault();
        ultimo.focus();
      } else if (!evento.shiftKey && document.activeElement === ultimo) {
        evento.preventDefault();
        primero.focus();
      }
    };
    document.addEventListener('keydown', alTeclear);
    return () => document.removeEventListener('keydown', alTeclear);
  }, [activo, ref]);
}
