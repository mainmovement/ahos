"use client"

import { ThemeProvider as NextThemesProvider } from "next-themes"
import { type ThemeProviderProps } from "next-themes/dist/types"
import { Toaster } from "@/components/ui/sonner"
import { DirectionProvider } from "./command_center/components/context/direction-provider"
import { FontProvider } from "./command_center/components/context/font-provider"
import { SearchProvider } from "./command_center/components/context/search-provider"
import { LayoutProvider } from "./command_center/components/context/layout-provider"

export function Providers({ children, ...props }: ThemeProviderProps) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="ahos"
      enableSystem={false}
      {...props}
    >
      <LayoutProvider>
        <SearchProvider>
          <DirectionProvider>
            <FontProvider>
              {children}
              <Toaster />
            </FontProvider>
          </DirectionProvider>
        </SearchProvider>
      </LayoutProvider>
    </NextThemesProvider>
  )
}