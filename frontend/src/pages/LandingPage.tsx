import { Link } from 'react-router-dom'

export default function LandingPage() {
  return (
    <div className="min-h-screen relative flex flex-col text-white">
      {/* Hero background */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{ backgroundImage: 'url(/images/1Z2A5708.webp)' }}
        aria-hidden
      />
      {/* Soft gradient overlay for legibility */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/40 to-black/70"
        aria-hidden
      />

      {/* Top brand bar */}
      <header className="relative z-10 px-6 sm:px-10 py-6 flex items-center justify-between">
        <img
          src="/salon-lyol-logo.png"
          alt="Salon Lyol"
          className="h-10 w-auto"
        />
        <Link
          to="/login"
          className="text-sm tracking-widest uppercase text-white/80 hover:text-white transition-colors"
        >
          Sign in
        </Link>
      </header>

      {/* Main content */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6 text-center -mt-20">
        <p
          className="text-xs sm:text-sm tracking-[0.4em] uppercase text-white/70 mb-6"
        >
          Toronto · Yonge Street
        </p>
        <h1
          className="text-5xl sm:text-7xl font-light leading-tight max-w-3xl"
          style={{ fontFamily: 'var(--font-display)' }}
        >
          Every day can be a<br />
          <em className="font-normal">good hair day.</em>
        </h1>
        <p className="mt-6 text-base sm:text-lg text-white/80 font-light max-w-md">
          Boutique colour, cuts, and styling — by appointment.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-3 w-full max-w-md">
          <Link
            to="/register"
            className="flex-1 inline-flex items-center justify-center rounded-sm bg-white text-neutral-900 text-sm tracking-widest uppercase font-medium px-8 py-4 hover:bg-white/90 transition-colors"
          >
            Request an appointment
          </Link>
          <Link
            to="/login"
            className="sm:hidden flex-1 inline-flex items-center justify-center rounded-sm border border-white/40 text-sm tracking-widest uppercase font-medium px-8 py-4 hover:bg-white/10 transition-colors"
          >
            Sign in
          </Link>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 px-6 sm:px-10 py-6 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-white/60">
        <p className="tracking-wider">1452 Yonge Street · Toronto, ON</p>
        <a
          href="https://salonlyol.ca"
          className="tracking-wider hover:text-white transition-colors"
        >
          salonlyol.ca
        </a>
      </footer>
    </div>
  )
}
