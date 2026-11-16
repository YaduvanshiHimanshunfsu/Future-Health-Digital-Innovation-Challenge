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
export type ChatReply = Schemas["ChatOut"];
export type Options = Schemas["OptionsOut"];
export type Values = Schemas["ValuesOut"];
export type QueueItem = Schemas["QueueItemOut"];
export type Journey = Schemas["JourneyOut"];
export type Slot = Schemas["SlotOut"];
export type Counsellor = Schemas["CounsellorOut"];
export type Appointment = Schemas["AppointmentOut"];
export type StaffAppointment = Schemas["StaffAppointmentOut"];
export type Referral = Schemas["ReferralOut"];
export type Centres = Schemas["CentresOut"];
export type InstrumentQuestions = Schemas["InstrumentOut"];
export type Score = Schemas["ScoreOut"];
export type MyScores = Schemas["MyScoresOut"];
export type Analytics = Schemas["AnalyticsOut"];

export type IconArrayVisual = {
  type: "icon_array";
  total: number;
  gene: string | null;
  groups: { key: string; count: number }[];
};
export type PunnettVisual = {
  type: "punnett";
  /** Which letters the square uses: on a dominant square the capital is the changed copy. */
  pattern: "recessive" | "dominant";
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
