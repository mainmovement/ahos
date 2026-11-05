import { cn } from "@/lib/utils";

/**
 * Context-sensitive page header: eyebrow, title, description, actions.
 * Eyebrow letterspacing is applied only to Latin text (Arabic script must
 * never be letter-spaced).
 */
export function PageHeader({
  eyebrow,
  eyebrowLatin,
  title,
  description,
  actions,
  className,
}: {
  eyebrow?: string;
  eyebrowLatin?: string;
  title: string;
  description?: string;
  actions?: React.ReactNode;
  className?: string;
}) {
  return (
    <header className={cn("mb-6 flex flex-wrap items-end justify-between gap-4", className)}>
      <div className="min-w-0 max-w-2xl">
        {eyebrow || eyebrowLatin ? (
          <p className={cn("eyebrow mb-1.5", eyebrowLatin && "eyebrow--latin")} dir={eyebrowLatin ? "ltr" : undefined}>
            {eyebrowLatin ?? eyebrow}
          </p>
        ) : null}
        <h1 className="text-2xl font-extrabold leading-tight tracking-tight">{title}</h1>
        {description ? (
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  );
}
