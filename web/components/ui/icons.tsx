/**
 * One icon vocabulary for the whole app.
 *
 * Phosphor at bold weight, so every glyph carries the same stroke as the
 * 1px rules around it. Importing from the `/ssr` entry keeps the set usable
 * from server components; nothing here reads Phosphor's icon context.
 */
import type { ComponentProps } from "react";
import {
  ArrowCounterClockwise,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  ArrowSquareOut,
  ArrowUp,
  ArrowUpRight,
  ArrowsOutSimple,
  Bank,
  Binoculars,
  BracketsCurly,
  Buildings,
  Calculator,
  CaretDown,
  CaretRight,
  ChatTeardropDots,
  Check,
  CheckCircle,
  Clock,
  CloudRain,
  Database,
  Eye,
  Faders,
  FileDashed,
  FileMagnifyingGlass,
  FileText,
  Flask,
  FunnelSimple,
  Gauge,
  GitBranch,
  Info,
  List,
  MagnifyingGlass,
  MinusCircle,
  Moon,
  Newspaper,
  NotePencil,
  PaperPlaneTilt,
  Prohibit,
  Pulse,
  Question,
  Scales,
  SealCheck,
  ShieldCheck,
  SlidersHorizontal,
  SquaresFour,
  Sun,
  Table,
  ThumbsDown,
  ThumbsUp,
  ToggleLeft,
  ToggleRight,
  Trash,
  TreeStructure,
  User,
  Warning,
  WarningCircle,
  X,
} from "@phosphor-icons/react/ssr";

type Glyph = typeof ArrowRight;
export type IconProps = Omit<ComponentProps<Glyph>, "weight">;

function icon(Glyph: Glyph, name: string) {
  function Wrapped(props: IconProps) {
    return <Glyph weight="bold" aria-hidden="true" {...props} />;
  }
  Wrapped.displayName = name;
  return Wrapped;
}

/* Navigation and chrome */
export const IconToday = icon(SquaresFour, "IconToday");
export const IconCompanies = icon(Buildings, "IconCompanies");
export const IconImpact = icon(TreeStructure, "IconImpact");
export const IconCopilot = icon(ChatTeardropDots, "IconCopilot");
export const IconAgent = icon(Faders, "IconAgent");
export const IconMethod = icon(Flask, "IconMethod");
export const IconMenu = icon(List, "IconMenu");
export const IconClose = icon(X, "IconClose");
export const IconSun = icon(Sun, "IconSun");
export const IconMoon = icon(Moon, "IconMoon");

/* Movement */
export const IconArrowRight = icon(ArrowRight, "IconArrowRight");
export const IconArrowLeft = icon(ArrowLeft, "IconArrowLeft");
export const IconArrowUp = icon(ArrowUp, "IconArrowUp");
export const IconArrowDown = icon(ArrowDown, "IconArrowDown");
export const IconArrowUpRight = icon(ArrowUpRight, "IconArrowUpRight");
export const IconCaretDown = icon(CaretDown, "IconCaretDown");
export const IconCaretRight = icon(CaretRight, "IconCaretRight");
export const IconExternal = icon(ArrowSquareOut, "IconExternal");
export const IconExpand = icon(ArrowsOutSimple, "IconExpand");
export const IconUndo = icon(ArrowCounterClockwise, "IconUndo");

/* Evidence state */
export const IconVerified = icon(CheckCircle, "IconVerified");
export const IconCheck = icon(Check, "IconCheck");
export const IconConflict = icon(Warning, "IconConflict");
export const IconAttention = icon(WarningCircle, "IconAttention");
export const IconUnknown = icon(Question, "IconUnknown");
export const IconNeutral = icon(MinusCircle, "IconNeutral");
export const IconGate = icon(ShieldCheck, "IconGate");
export const IconSeal = icon(SealCheck, "IconSeal");
export const IconBlocked = icon(Prohibit, "IconBlocked");

/* Data and instruments */
export const IconSource = icon(Database, "IconSource");
export const IconDocument = icon(FileText, "IconDocument");
export const IconDraftData = icon(FileDashed, "IconDraftData");
export const IconInspect = icon(FileMagnifyingGlass, "IconInspect");
export const IconCalculator = icon(Calculator, "IconCalculator");
export const IconTable = icon(Table, "IconTable");
export const IconSignal = icon(Pulse, "IconSignal");
export const IconGauge = icon(Gauge, "IconGauge");
export const IconClock = icon(Clock, "IconClock");
export const IconCode = icon(BracketsCurly, "IconCode");
export const IconScales = icon(Scales, "IconScales");

/* Domain */
export const IconNews = icon(Newspaper, "IconNews");
export const IconWeather = icon(CloudRain, "IconWeather");
export const IconPolicy = icon(Bank, "IconPolicy");
export const IconBranch = icon(GitBranch, "IconBranch");
export const IconGraph = icon(TreeStructure, "IconGraph");

/* Controls */
export const IconSearch = icon(MagnifyingGlass, "IconSearch");
export const IconFilter = icon(FunnelSimple, "IconFilter");
export const IconSliders = icon(SlidersHorizontal, "IconSliders");
export const IconSend = icon(PaperPlaneTilt, "IconSend");
export const IconTrash = icon(Trash, "IconTrash");
export const IconToggleOn = icon(ToggleRight, "IconToggleOn");
export const IconToggleOff = icon(ToggleLeft, "IconToggleOff");
export const IconThumbsUp = icon(ThumbsUp, "IconThumbsUp");
export const IconThumbsDown = icon(ThumbsDown, "IconThumbsDown");
export const IconNote = icon(NotePencil, "IconNote");
export const IconWatch = icon(Eye, "IconWatch");
export const IconUser = icon(User, "IconUser");
export const IconInfo = icon(Info, "IconInfo");
export const IconEmpty = icon(Binoculars, "IconEmpty");
