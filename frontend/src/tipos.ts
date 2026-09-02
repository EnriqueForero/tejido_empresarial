export type ModoBusqueda = 'filters' | 'business_name' | 'nit' | 'batch_nits';

export type DefinicionFiltro = {
  key: string;
  query_column?: string;
  label: string;
  group: string;
  help?: string;
  options?: string[];
  truncated?: boolean;
};

export type SolicitudBusqueda = {
  mode: ModoBusqueda;
  filters: Record<string, string[]>;
  term: string;
  nits: string[];
  page: number;
  page_size: number;
};

export type Fila = Record<string, string | number | null>;

export type RespuestaBusqueda = {
  total: number;
  page: number;
  page_size: number;
  page_count: number;
  preview_truncated: boolean;
  columns: string[];
  rows: Fila[];
  summary: string;
  demo: boolean;
};

export type Fuente = { name: string; detail: string; cut: string };

export type Metadatos = {
  title: string;
  version: string;
  demo: boolean;
  data_connection: 'demo' | 'configured' | 'missing_configuration' | 'connected';
  preview_columns: string[];
  export_columns: string[];
  column_sections: Array<{ title: string; columns: string[] }>;
  sources: Fuente[];
  periods: Record<string, string>;
  notes: string[];
  filters: DefinicionFiltro[];
  filter_groups: string[];
  export_max_rows: number;
  preview_max_rows: number;
  batch_max_nits: number;
  contact_fields_included: boolean;
};

export type EntradaGlosario = {
  variable: string;
  description: string;
  description_paragraphs: string[];
  sources: string;
  category: string;
  in_export: boolean;
  in_preview: boolean;
  filter_key: string | null;
  filter_label: string | null;
  origin: 'glosario' | 'aplicativo';
};

export type RespuestaGlosario = {
  entries: EntradaGlosario[];
  count: number;
  institutional_count: number;
  supplementary_count: number;
  categories: string[];
  coverage: { export_columns: number; defined_export_columns: number; missing: string[] };
  updated_at: string;
  file_name: string;
};

export type Ficha = {
  nit: string;
  record: Fila;
  sections: Array<{ title: string; fields: Array<{ name: string; value: string | number | null }> }>;
  matches: number;
  demo: boolean;
};

export type Salud = {
  status: string;
  version: string;
  data_connection: Metadatos['data_connection'];
  access_control: 'basic' | 'open';
  frontend_built: boolean;
};
