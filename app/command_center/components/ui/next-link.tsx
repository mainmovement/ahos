'use client'

import NextLink from 'next/link'
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

interface NextLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string
  disabled?: boolean
}

const NextLinkBase = forwardRef<HTMLAnchorElement, NextLinkProps>(
  ({ href, disabled, className, ...props }, ref) => {
    if (disabled) {
      return (
        <span
          ref={ref}
          className={cn(
            'cursor-not-allowed select-none text-muted-foreground',
            className
          )}
          {...props}
        />
      )
    }

    return (
      <NextLink
        ref={ref}
        href={href}
        className={className}
        {...props}
      />
    )
  }
)

NextLinkBase.displayName = 'NextLink'

export { NextLinkBase as NextLink }