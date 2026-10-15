'use client'

import React, { createContext, useContext, useState, ReactNode } from 'react'

interface SearchContextType {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  query: string
  setQuery: (query: string) => void
}

const SearchContext = createContext<SearchContextType | undefined>(undefined)

export function SearchProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')

  return (
    <SearchContext.Provider value={{ isOpen, setIsOpen, query, setQuery }}>
      {children}
    </SearchContext.Provider>
  )
}

export function useSearch() {
  const context = useContext(SearchContext)
  if (context === undefined) {
    throw new Error('useSearch must be used within a SearchProvider')
  }
  return context
}