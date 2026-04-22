import { Link } from 'react-router-dom'
import { Button } from '@/components/ui/button'

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'linear-gradient(160deg, #faf9f7 0%, #f0ece4 100%)' }}>
      {/* Main content */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 text-center">
        <img
          src="/salon-lyol-logo.png"
          alt="Salon Lyol"
          className="h-48 w-auto mb-8 drop-shadow-sm"
        />

        <p className="text-muted-foreground text-lg mb-2 font-light tracking-wide">
          Toronto's boutique hair salon
        </p>
        <p className="text-muted-foreground text-sm mb-10 max-w-xs">
          Expert colour, cuts, and styling by appointment.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 w-full max-w-xs">
          <Button asChild size="lg" className="flex-1 text-base">
            <Link to="/register">Request an appointment</Link>
          </Button>
          <Button asChild size="lg" variant="outline" className="flex-1 text-base">
            <Link to="/login">Sign in</Link>
          </Button>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-6 text-center text-xs text-muted-foreground/60 space-y-1">
        <p>Salon Lyol · Toronto, ON</p>
        <p>
          <a href="https://salonlyol.ca" className="hover:underline">salonlyol.ca</a>
        </p>
      </footer>
    </div>
  )
}
