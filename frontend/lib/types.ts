export interface Message {
  role: "user" | "assistant";
  content: TextParagraph[] | string;
}

export enum SourceType {
  LAW = "law",
  CASE_LAW = "case_law",
  TAXONOMY = "taxonomy",
  WERKINSTRUCTIE = "werkinstructie",
  SELECTIELIJST = "selectielijst",
}

export enum SourceTypeLabel {
  LAW = "Wet",
  CASE_LAW = "Jurisprudentie",
  TAXONOMY = "Definitie",
  WERKINSTRUCTIE = "Werkinstructie",
  SELECTIELIJST = "Selectielijst",
}

interface BaseSource {
  id?: string;
  type: SourceType;
}

interface ISelectielijstRow {
  selectielijsten: string;
  procescategorie: string;
  process_number: string;
  process_description: string;
  waardering: string;
  toelichting: string;
  voorbeelden: string;
  voorbeelden_werkdoc_bsd: string;
  persoonsgegevens_aanwezig: string;
  isSource: boolean;
}

interface ISelectielijst {
  name: string;
  rows: ISelectielijstRow[];
}

interface IWerkinstructie {
  title: string;
  url: string;
  isSource: boolean;
  chunks: string[];
}

interface ILaw {
  document?: string;
  title: string;
  law: string;
  url?: string;
  isSource: boolean;
  // eslint-disable-next-line @typescript-eslint/no-empty-object-type
  lido?: {};
}

interface ICaseLaw {
  document?: string;
  title: string;
  url: string;
  isSource: boolean;
  inhoudsindicatie?: string;
  date_uitspraak?: string;
}

interface ITaxonomy {
  label: string;
  context: Array<{
    id: string;
    isSource: boolean;
    source: string;
    definition: string;
    naderToegelicht: string[];
    wetcontext: {
      url: string;
    };
  }>;
}

// Specifieke source types
export interface LawSource extends BaseSource {
  type: SourceType.LAW;
  value: ILaw;
}

export interface WerkinstructieSource extends BaseSource {
  type: SourceType.WERKINSTRUCTIE;
  value: IWerkinstructie;
}

export interface CaseLawSource extends BaseSource {
  type: SourceType.CASE_LAW;
  value: ICaseLaw;
}

export interface TaxonomySource extends BaseSource {
  type: SourceType.TAXONOMY;
  value: ITaxonomy;
}

export interface SelectielijstSource extends BaseSource {
  id: string;
  type: SourceType.SELECTIELIJST;
  value: ISelectielijst;
}

// Union type voor alle sources (use type instead of interface)
export type Source =
  | LawSource
  | CaseLawSource
  | TaxonomySource
  | SelectielijstSource
  | WerkinstructieSource;

// Text paragraph interface
export interface TextParagraph {
  paragraph: string;
  sources: string[];
}

// Answer interface
export interface Answer {
  text: TextParagraph[];
  sources: Source[];
}

// Root data interface
export interface LegalData {
  answer: Answer;
  sources: Source[];
}

// Filter type
export type TFilter = SourceType | "answer" | "all";

// Agenda/Calendar types
export interface AgendaEvent {
  id: number | string;
  title: string;
  date: string;
  dayOfWeek: string;
  start: string;
  end: string;
  timeZone: string;
  organizer: string;
  meetingLocation: string;
  relatedToDossier: string | null;
  link: string | null;
}

export interface AgendaDay {
  date: string; // YYYY-MM-DD
  events: AgendaEvent[];
}

export type AgendaWeek = Record<string, AgendaDay>;

export interface RelatedTo {
  type: string;
  title: string;
  url: string;
}

export interface Task {
  id: string;
  title: string;
  dueDate: string | null;
  status: "notStarted" | "inProgress" | "waitinOnOthers" | "completed";
  relatedTo?: RelatedTo;
}

export interface DocumentItem {
  id?: string;
  name: string;
  filetype: string;
  url: string;
  linked_dossier: string;
  is_transcript?: boolean;
  show_magic_wand?: boolean;
  nextcloud_id?: string;
}

export interface DossierItem {
  dossier_id: string;
  name: string;
  url: string;
  progress: number;
  linked_zaak: string;
  last_modified: string;
  is_unopened: boolean;
  date_received: string;
  file_id?: string;
}

export interface SearchResultHit {
  _index: string;
  _id: string;
  _score: number;
  _ignored?: string[];
  _source: {
    title: string;
    raw_title: string;
    url: string;
    datetime_published: string;
    created_date: string;
    lastmodifiedtime: string;
    sharepoint_id: string;
    drive_id: string;
    author: string;
    author_id: string;
    lastmodified_user_id: string;
    size: string;
    author_modified: string;
    filepath: string;
    filetype: string;
    needs_download: string;
    needs_annotation: string;
    keywords: string[];
    summary: string;
    werkprocess?: string;
    retention_period?: string;
    weight?: string;
    bewaartermijn: string;
    last_annotated: string;
    full_text: string;
    paragraphs: { id: number; text: string }[];
    accessible_to_users: string[];
    topics: string[];
    dossier_id?: string;
    dossier_name?: string;
    number_pages?: string;
  };
}

export interface SearchResultsResponse {
  results: number;
  hits: SearchResultHit[];
  aggregations?: Record<string, any>;
}

// Dashboard search filters type
export type DashboardSearchFilters = Record<string, string>;

// Dossier summary types
export interface DossierSummary {
  dossier_id: string;
  summary: string;
  nextStep: string;
  followUpQuestions: string[];
}

export interface DossierSummaryResponse {
  success: boolean;
  data?: DossierSummary;
  error?: string;
}

// Document processing types
export interface DocumentProcessingOptions {
  document_id: string;
  options: {
    generate_closure_letter: boolean;
    generate_summary: boolean;
  };
}

export interface DocumentProcessingResponse {
  success: boolean;
  data?: {
    closure_letter_url?: string;
    summary_url?: string;
  };
  error?: string;
}
