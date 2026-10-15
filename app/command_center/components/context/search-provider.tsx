'use client'

import { createContext, useContext, useEffect, useState } from 'react'
import { CommandMenu } from '@/app/command_center/components/command-menu'

type SearchContextType = {
  open: boolean
  setIsOpen: React.Dispatch<React.SetStateAction<boolean>>
}

const SearchContext = createContext<SearchContextType | null>(null)

type SearchProviderProps = {
  children: React.ReactNode
}

export function SearchProvider({ children }: SearchProviderProps) {
  const [open, setIsOpen] = useState(false)

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setIsOpen((open) => !open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [])

  return (
    <SearchContext value={{ open, setIsOpen }}>
      {children}
      <CommandMenu />
    </SearchContext>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export const useSearch = () => {
  const searchContext = useContext(SearchContext)

  if (!searchContext) {
    throw new Error('useSearch has to be used within SearchProvider')
  }

  return searchContext
}
