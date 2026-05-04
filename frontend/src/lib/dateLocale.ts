import { useTranslation } from 'react-i18next'
import { fr as dateFnsFr, enCA } from 'date-fns/locale'
import type { Locale } from 'date-fns'

const LOCALE_MAP: Record<string, Locale> = {
  fr: dateFnsFr,
  en: enCA,
}

/** Returns the date-fns Locale and BCP-47 string for the active i18n language. */
export function useDateLocale(): { locale: Locale; bcp47: string } {
  const { i18n } = useTranslation()
  const lang = i18n.language ?? 'en'
  return {
    locale: LOCALE_MAP[lang] ?? enCA,
    bcp47:  lang === 'fr' ? 'fr-CA' : 'en-CA',
  }
}
