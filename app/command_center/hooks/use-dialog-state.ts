'use client'

import { useState, useCallback } from 'react'

export function useDialogState() {
  const [open, setOpen] = useState(false)
  const [dialogType, setDialogType] = useState<'confirm' | 'info' | 'warning'>('info')

  const openDialog = useCallback((type: 'confirm' | 'info' | 'warning' = 'info') => {
    setDialogType(type)
    setOpen(true)
  }, [])

  const closeDialog = useCallback(() => {
    setOpen(false)
  }, [])

  const toggleDialog = useCallback(() => {
    setOpen(prev => !prev)
  }, [])

  return {
    open,
    dialogType,
    openDialog,
    closeDialog,
    toggleDialog,
  }
}