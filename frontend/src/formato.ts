/**
 * Formato de valores para pantalla (es-CO): separador de miles con punto,
 * decimales con coma, identificadores sin formato numérico.
 */
const entero = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 0 });
const decimal2 = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const decimal1 = new Intl.NumberFormat('es-CO', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

const PALABRAS_IDENTIFICADOR = ['NIT', 'Código', 'Dígito', 'ID del', 'posición arancelaria estrella'];

export const esIdentificador = (columna: string) => PALABRAS_IDENTIFICADOR.some((palabra) => columna.includes(palabra));
export const esMonetaria = (columna: string) => columna.includes('(COP)') || columna.includes('FOB USD');
export const esNumericaVisual = (columna: string, valor: unknown) => typeof valor === 'number' && !esIdentificador(columna);

export function formatearValor(valor: unknown, columna: string): string {
  if (valor === null || valor === undefined || valor === '') return '—';
  if (typeof valor === 'number') {
    if (esIdentificador(columna)) return String(valor);
    if (columna.includes('FOB USD')) return `USD ${decimal2.format(valor)}`;
    if (columna.includes('(COP)')) return `$ ${entero.format(valor)}`;
    if (columna === 'Antigüedad de la empresa (años)') return decimal1.format(valor);
    if (columna.includes('Índice')) return decimal2.format(valor);
    if (columna.includes('Distancia')) return valor.toFixed(4).replace('.', ',');
    return Number.isInteger(valor) ? entero.format(valor) : decimal2.format(valor);
  }
  return String(valor);
}

/** Cifra abreviada legible en español: 8,4 M · 998 k · 257.716 millones. */
export function abreviar(valor: number, estilo: 'M' | 'millones' = 'M'): string {
  const abs = Math.abs(valor);
  if (estilo === 'millones') {
    if (abs >= 1e12) return `${decimal1.format(valor / 1e12)} billones`;
    if (abs >= 1e9) return `${entero.format(Math.round(valor / 1e6))} millones`;
    if (abs >= 1e7) return `${decimal1.format(valor / 1e6)} millones`;
    if (abs >= 1e6) return `${decimal2.format(valor / 1e6)} millones`;
    return entero.format(valor);
  }
  if (abs >= 1e9) return `${decimal1.format(valor / 1e9)} mil M`;
  if (abs >= 1e6) return `${decimal1.format(valor / 1e6)} M`;
  if (abs >= 1e3) return `${entero.format(Math.round(valor / 1e3))} k`;
  return entero.format(valor);
}

/** Versión corta para tarjetas y cifras destacadas. */
export function formatearCompacto(valor: unknown, columna: string): string {
  if (typeof valor !== 'number' || esIdentificador(columna)) return formatearValor(valor, columna);
  if (columna.includes('FOB USD')) return valor === 0 ? 'USD 0' : `USD ${abreviar(valor)}`;
  if (columna.includes('(COP)')) return `$ ${abreviar(valor, 'millones')}`;
  return formatearValor(valor, columna);
}

export const formatearEntero = (valor: number) => entero.format(valor);

/** Etiqueta corta de columna para encabezados de tabla y tarjetas. */
export function etiquetaCorta(columna: string): string {
  return columna
    .replace('Exportaciones totales de la empresa ', 'Exportaciones ')
    .replace(' - Actividad principal', ' · act. principal')
    .replace('Rev 4', 'Rev. 4')
    .replace('Descripción CIIU', 'Actividad CIIU');
}

export function limpiarNit(valor: string): string {
  return valor.replace(/\D/g, '');
}
