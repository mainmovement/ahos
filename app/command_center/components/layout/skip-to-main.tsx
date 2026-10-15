import { cn } from '@/lib/utils'

type SkipToMainProps = {
  skipTo?: string
  className?: string
}

export function SkipToMain({
  skipTo = '#main-content',
  className,
}: SkipToMainProps) {
  return (
    <a
      href={skipTo}
      className={cn(
        'sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground',
        className
      )}
    >
      Skip to content
    </a>
  )
}