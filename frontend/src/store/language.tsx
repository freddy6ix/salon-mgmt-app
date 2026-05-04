import { createContext, useContext, useState, type ReactNode } from 'react'

// Module-level variable so api/client.ts can read it without React hooks
let _sessionLanguage: string | null = null

export function getSessionLanguage(): string | null {
  return _sessionLanguage
}

export function resetSessionLanguage(): void {
  _sessionLanguage = null
}

interface LanguageState {
  sessionLanguage: string | null
  setSessionLanguage: (lang: string | null) => void
}

const LanguageContext = createContext<LanguageState | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [sessionLanguage, setLang] = useState<string | null>(null)

  function setSessionLanguage(lang: string | null) {
    _sessionLanguage = lang
    setLang(lang)
  }

  return (
    <LanguageContext.Provider value={{ sessionLanguage, setSessionLanguage }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageState {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used inside LanguageProvider')
  return ctx
}
