import { useState, useEffect } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getBranding, updateBranding, type BrandingSettings } from '@/api/settings'
import { Button } from '@/components/ui/button'
import { applyBranding } from '@/lib/branding'

export default function SettingsPage() {
  const qc = useQueryClient()

  const { data: branding, isLoading } = useQuery({
    queryKey: ['branding'],
    queryFn: getBranding,
  })

  const [logoUrl, setLogoUrl] = useState('')
  const [brandColor, setBrandColor] = useState('#18181b')

  useEffect(() => {
    if (branding) {
      setLogoUrl(branding.logo_url ?? '')
      setBrandColor(branding.brand_color ?? '#18181b')
    }
  }, [branding])

  const mutation = useMutation({
    mutationFn: () => updateBranding({
      logo_url: logoUrl || null,
      brand_color: brandColor,
    }),
    onSuccess: (updated: BrandingSettings) => {
      qc.setQueryData(['branding'], updated)
      applyBranding(updated)
    },
  })

  if (isLoading) return <div className="p-6 text-sm text-muted-foreground">Loading…</div>

  return (
    <div className="p-6 max-w-2xl space-y-8">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Manage your salon configuration.</p>
      </div>

      {/* Branding */}
      <section className="border rounded-lg p-5 space-y-5 bg-white">
        <h2 className="text-base font-medium">Branding</h2>

        {/* Logo */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Logo URL</label>
          <input
            type="url"
            value={logoUrl}
            onChange={e => setLogoUrl(e.target.value)}
            placeholder="https://example.com/logo.png"
            className="w-full border border-input rounded-md px-3 py-2 text-sm bg-background"
          />
          <p className="text-xs text-muted-foreground">
            Paste a publicly accessible image URL. Recommended: square PNG or SVG, transparent background.
          </p>
          {logoUrl && (
            <div className="flex items-center gap-4 pt-1">
              <img src={logoUrl} alt="Logo preview" className="h-12 w-auto object-contain border rounded p-1 bg-muted/30" onError={e => (e.currentTarget.style.display = 'none')} />
              <span className="text-xs text-muted-foreground">Preview</span>
            </div>
          )}
        </div>

        {/* Brand colour */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Brand colour</label>
          <div className="flex items-center gap-3">
            <input
              type="color"
              value={brandColor}
              onChange={e => setBrandColor(e.target.value)}
              className="h-9 w-16 cursor-pointer rounded border border-input p-0.5 bg-background"
            />
            <input
              type="text"
              value={brandColor}
              onChange={e => {
                const v = e.target.value
                if (/^#[0-9a-fA-F]{0,6}$/.test(v)) setBrandColor(v)
              }}
              className="w-28 border border-input rounded-md px-3 py-2 text-sm bg-background font-mono"
              maxLength={7}
            />
            <div
              className="h-9 w-24 rounded border border-input text-xs flex items-center justify-center font-medium"
              style={{ backgroundColor: brandColor.length === 7 ? brandColor : undefined }}
            >
              <span style={{ color: colorIsDark(brandColor) ? '#fff' : '#000' }}>Button</span>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">Applied to buttons and accents throughout the app.</p>
        </div>

        {mutation.isError && (
          <p className="text-xs text-destructive">
            {mutation.error instanceof Error ? mutation.error.message : 'Save failed'}
          </p>
        )}

        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? 'Saving…' : 'Save branding'}
        </Button>
      </section>
    </div>
  )
}

function colorIsDark(hex: string): boolean {
  if (hex.length !== 7) return true
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return (0.299 * r + 0.587 * g + 0.114 * b) / 255 < 0.5
}
