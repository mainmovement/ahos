import { tr } from "@/src/lib/i18n";

/** tr() with {name} placeholders: trf("newsroom.fmt.sources", { n: 3 }). */
export function trf(path: string, vars: Record<string, string | number> = {}): string {
  return tr("fa", path).replace(/\{(\w+)\}/g, (_m, k: string) => (k in vars ? String(vars[k]) : `{${k}}`));
}
