import type { components } from "./schema";

type Schemas = components["schemas"];
export type Fact = Schemas["FactOut"];
export type MyResults = Schemas["MyResultsOut"];
export type MyRisk = Schemas["MyRiskOut"];
export type CareStep = Schemas["CareStepOut"];
export type Profile = Schemas["ProfileOut"];
export type Pack = Schemas["PackOut"];
export type Consent = Schemas["ConsentOut"];
export type ConsentList = Schemas["ConsentListOut"];
export type AccessEntry = Schemas["AccessEntryOut"];
export type AccessLog = Schemas["AccessLogOut"];
export type Couple = Schemas["CoupleOut"];
export type Match = Schemas["MatchOut"];
export type SharedFull = Schemas["SharedFullOut"];
export type SharedSummary = Schemas["SharedSummaryOut"];
export type InvitePage = Schemas["InvitePageOut"];
export type CaseView = Schemas["CaseOut"];
export type BreakGlassEvent = Schemas["BreakGlassEventOut"];

export type IconArrayVisual = {
  type: "icon_array";
  total: number;
  gene: string | null;
  groups: { key: string; count: number }[];
};
export type PunnettVisual = {
  type: "punnett";
  gene: string | null;
  parent_a: string[];
  parent_b: string[];
  cells: string[][];
  legend: Record<string, string>;
};
export type XLinkedVisual = {
  type: "x_linked";
  gene: string | null;
  children: { key: string; percent: string }[];
};
export type Visual = IconArrayVisual | PunnettVisual | XLinkedVisual;
