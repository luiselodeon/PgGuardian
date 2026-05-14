import { useState } from 'react'
import logo from '../assets/Logo.png'

export default function LandingPage() {

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const features = [
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      ),
      title: 'Índices inteligentes',
      desc: 'Detecta FK sin índice, duplicados, índices no usados y oportunidades de índices parciales o de cobertura.'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
        </svg>
      ),
      title: 'Bloat y mantenimiento',
      desc: 'Mide el bloat real de tablas, detecta autovacuum deshabilitado y tuplas muertas que degradan el rendimiento.'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
      title: 'Queries problemáticas',
      desc: 'Encuentra sequential scans, queries lentas y operaciones que están consumiendo recursos innecesariamente.'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      title: 'Memoria y temp spills',
      desc: 'Evalúa work_mem, shared_buffers y detecta sort/hash spills en disco que afectan la velocidad de las consultas.'
    },
    {
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      title: 'Health Score',
      desc: 'Un puntaje del 0 al 100 que resume la salud de tu base de datos. Baja cuando hay hallazgos críticos sin atender.'
    }
  ]

  const whyItems = [
    {
      title: 'Pensado para PyMEs mexicanas',
      desc: 'No necesitas un DBA dedicado. En minutos obtienes un diagnóstico completo de tu base de datos.'
    },
    {
      title: 'Soporte en español',
      desc: 'Toda la interfaz, hallazgos y recomendaciones están en español. Sin barreras de idioma.'
    },
    {
      title: 'Opción self-hosted',
      desc: 'Despliegas PgGuardian en tu propia infraestructura con Docker Compose. Los datos nunca salen de tu red.'
    },
    {
      title: 'Sin agentes invasivos',
      desc: 'Conexión read-only a tu PostgreSQL. No instalamos agentes, no modificamos tablas, no afectamos rendimiento.'
    },
    {
      title: 'Recomendaciones accionables',
      desc: 'No solo te decimos qué está mal. Te damos SQL sugerido o pasos concretos para corregirlo y la prioridad de cada hallazgo.'
    }
  ]

  return (

    <div className="min-h-screen bg-white">

      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-sky/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8">
                <img src={logo} alt="PgGuardian" className="w-full h-full object-contain" />
              </div>
              <span className="text-xl font-bold text-primary">PgGuardian</span>
            </div>

            {/* Desktop nav */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-sm text-primary/70 hover:text-accent transition">Funcionalidades</a>
              <a href="#why" className="text-sm text-primary/70 hover:text-accent transition">Por qué PgGuardian</a>
              <a href="#pricing" className="text-sm text-primary/70 hover:text-accent transition">Precios</a>
              <button className="px-5 py-2 bg-accent text-white text-sm font-medium rounded-lg hover:bg-accent/90 transition shadow-sm">
                Solicitar demo
              </button>
            </div>

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-primary/70 hover:bg-sky"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {mobileMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-white border-t border-sky/50 px-4 py-4 space-y-3">
            <a href="#features" className="block text-sm text-primary/70 hover:text-accent" onClick={() => setMobileMenuOpen(false)}>Funcionalidades</a>
            <a href="#why" className="block text-sm text-primary/70 hover:text-accent" onClick={() => setMobileMenuOpen(false)}>Por qué PgGuardian</a>
            <a href="#pricing" className="block text-sm text-primary/70 hover:text-accent" onClick={() => setMobileMenuOpen(false)}>Precios</a>
            <button className="w-full px-5 py-2 bg-accent text-white text-sm font-medium rounded-lg hover:bg-accent/90 transition">
              Solicitar demo
            </button>
          </div>
        )}
      </nav>

      {/* HERO */}
      <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-sky via-white to-white" />
        <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-secondary/10 to-transparent" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent/10 text-accent text-xs font-medium rounded-full mb-6">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Auditoría automatizada para PostgreSQL
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold text-primary leading-tight mb-6">
              Detecta el problema antes de que tu PostgreSQL{' '}
              <span className="bg-gradient-to-r from-accent to-secondary bg-clip-text text-transparent">
                detenga tu negocio
              </span>
            </h1>

            <p className="text-lg md:text-xl text-primary/60 mb-10 leading-relaxed">
              PgGuardian se conecta en modo read-only, analiza la salud de tu base de datos 
              y convierte métricas complejas en hallazgos claros, priorizados y accionables.
            </p>

            <div className="flex flex-col sm:flex-row gap-4">
              <button className="px-8 py-3.5 bg-accent text-white font-semibold rounded-xl hover:bg-accent/90 transition shadow-lg shadow-accent/30 text-center">
                Solicitar demo
              </button>
              <a href="https://pgguardian-frontend.onrender.com/" target="_blank" rel="noopener noreferrer" className="px-8 py-3.5 border-2 border-primary/20 text-primary font-semibold rounded-xl hover:border-accent/50 hover:text-accent transition text-center inline-block">
                Ver cómo funciona
              </a>
            </div>

            {/* Trust indicators */}
            <div className="mt-12 flex flex-wrap items-center gap-8 text-sm text-primary/40">
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                Conexión read-only
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                Sin instalar agentes
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                22 detectores
              </span>
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                Recomendaciones SQL
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* PROBLEM SECTION */}
      <section className="py-20 md:py-28 bg-sky/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              ¿Por qué cuesta tanto mantener PostgreSQL saludable?
            </h2>
            <p className="text-lg text-primary/60 leading-relaxed">
              Sin un DBA dedicado, los problemas de base de datos se detectan cuando ya es tarde: 
              consultas lentas en producción, páginas que no cargan, reportes que no terminan.
            </p>
          </div>

          <div className="mt-16 grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-sky">
              <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-primary mb-2">No sabes lo que no sabes</h3>
              <p className="text-primary/60 text-sm">Hay más de 20 puntos ciegos en una BD PostgreSQL. La mayoría de las empresas los descubren por error.</p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-sm border border-sky">
              <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-primary mb-2">El DBA es caro y escaso</h3>
              <p className="text-primary/60 text-sm">Un DBA en México cuesta más de $40,000 MXN/mes. No todas las PyMEs pueden costearlo.</p>
            </div>

            <div className="bg-white rounded-2xl p-8 shadow-sm border border-sky">
              <div className="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-primary mb-2">El rendimiento se degrada lento</h3>
              <p className="text-primary/60 text-sm">Un índice faltante o un work_mem bajo no se notan hasta que tu app crece y empiezan los timeout.</p>
            </div>
          </div>
        </div>
      </section>

      {/* SOLUTION SECTION */}
      <section className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              Así funciona PgGuardian
            </h2>
            <p className="text-lg text-primary/60">
              En pocos minutos, PgGuardian analiza tu base de datos y te entrega un diagnóstico con evidencia, severidad y recomendaciones concretas.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12 max-w-4xl mx-auto">
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-sky flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">1</span>
              </div>
              <h3 className="font-semibold text-primary mb-2">Conecta</h3>
              <p className="text-primary/60 text-sm">PgGuardian se conecta a tu PostgreSQL con un usuario de solo lectura. No modificamos nada.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-sky flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">2</span>
              </div>
              <h3 className="font-semibold text-primary mb-2">Analiza</h3>
              <p className="text-primary/60 text-sm">Ejecuta 22 detectores en 5 categorías: índices, bloat, queries, configuración y salud general.</p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 rounded-full bg-sky flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-primary">3</span>
              </div>
              <h3 className="font-semibold text-primary mb-2">Corrige</h3>
              <p className="text-primary/60 text-sm">Cada hallazgo incluye severidad, evidencia y SQL sugerido o pasos concretos para resolverlo. Prioriza y actúa.</p>
            </div>
          </div>
        </div>
      </section>

      {/* FEATURES SECTION */}
      <section id="features" className="py-20 md:py-28 bg-sky/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              Auditoría completa en 5 categorías
            </h2>
            <p className="text-lg text-primary/60">
              Cada categoría tiene detectores específicos que buscan problemas reales en tu base de datos.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <div key={i} className="bg-white rounded-2xl p-6 shadow-sm border border-sky hover:shadow-md hover:border-accent/30 transition">
                <div className="w-12 h-12 rounded-xl bg-sky text-secondary flex items-center justify-center mb-4">
                  {f.icon}
                </div>
                <h3 className="text-lg font-semibold text-primary mb-2">{f.title}</h3>
                <p className="text-primary/60 text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* WHY PgGuardian */}
      <section id="why" className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              ¿Por qué PgGuardian?
            </h2>
            <p className="text-lg text-primary/60">
              No somos solo otro dashboard de métricas. Estamos construidos para equipos como el tuyo.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {whyItems.map((item, i) => (
              <div key={i} className="flex gap-4 p-6 rounded-2xl bg-white border border-sky hover:border-accent/30 transition">
                <div className="w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <svg className="w-3.5 h-3.5 text-accent" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                </div>
                <div>
                  <h3 className="font-semibold text-primary mb-1">{item.title}</h3>
                  <p className="text-primary/60 text-sm">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="py-20 md:py-28 bg-sky/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              Planes simples, sin sorpresas
            </h2>
            <p className="text-lg text-primary/60">
              Precios en pesos mexicanos. Sin contratos anuales. Cancela cuando quieras.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">

            {/* Inicial */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-sky flex flex-col">
              <h3 className="text-lg font-semibold text-primary mb-1">Inicial</h3>
              <p className="text-sm text-primary/50 mb-4">Para equipos que inician</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-primary">$850</span>
                <span className="text-primary/50 ml-1">/mes</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  1 instancia monitoreada
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Scans semanales automáticos
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Dashboard con health score
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Alertas por correo
                </li>
              </ul>
              <button className="w-full py-2.5 border-2 border-primary/20 text-primary font-medium rounded-xl hover:border-accent/50 hover:text-accent transition">
                Empezar
              </button>
            </div>

            {/* Pro - featured */}
            <div className="bg-white rounded-2xl p-8 shadow-lg border-2 border-accent flex flex-col relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-accent text-white text-xs font-semibold rounded-full">
                MÁS ELEGIDO
              </div>
              <h3 className="text-lg font-semibold text-primary mb-1">Pro</h3>
              <p className="text-sm text-primary/50 mb-4">Para startups en crecimiento</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-primary">$2,000</span>
                <span className="text-primary/50 ml-1">/mes</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Hasta 5 instancias
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Scans diarios automáticos
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Alertas por Slack
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Soporte prioritario
                </li>
              </ul>
              <button className="w-full py-2.5 bg-accent text-white font-medium rounded-xl hover:bg-accent/90 transition shadow-lg shadow-accent/30">
                Elegir Pro
              </button>
            </div>

            {/* Empresarial */}
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-sky flex flex-col">
              <h3 className="text-lg font-semibold text-primary mb-1">Empresarial</h3>
              <p className="text-sm text-primary/50 mb-4">Para equipos con SLA exigentes</p>
              <div className="mb-6">
                <span className="text-4xl font-bold text-primary">$4,500</span>
                <span className="text-primary/50 ml-1">/mes</span>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Self-hosted on-premise
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  SSO y control de accesos
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Auditoría customizable
                </li>
                <li className="flex items-start gap-2 text-sm text-primary/60">
                  <svg className="w-4 h-4 text-accent mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" /></svg>
                  Soporte dedicado 24/7
                </li>
              </ul>
              <button className="w-full py-2.5 border-2 border-primary/20 text-primary font-medium rounded-xl hover:border-accent/50 hover:text-accent transition">
                Contactar
              </button>
            </div>

          </div>
        </div>
      </section>

      {/* VALIDATION */}
      <section className="py-20 md:py-28">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-3xl mx-auto text-center">
            <div className="w-16 h-16 rounded-2xl bg-sky flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h2 className="text-3xl md:text-4xl font-bold text-primary mb-6">
              Validado con profesionales del sector
            </h2>
            <p className="text-lg text-primary/60 leading-relaxed mb-8">
              El problema fue validado con profesionales de bases de datos, infraestructura 
              y gestión técnica en México. Las entrevistas confirmaron que muchos equipos 
              detectan problemas de PostgreSQL de forma reactiva, cuando ya hay lentitud, 
              bloqueos o reportes de usuarios.
            </p>
            <div className="flex flex-wrap justify-center gap-8 text-sm text-primary/50">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                DBA consultados
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-secondary" />
                Líderes de infraestructura
              </span>
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Desarrolladores backend
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="py-20 md:py-28 bg-gradient-to-br from-primary via-[#050a62] to-primary">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6 leading-tight">
            Tu PostgreSQL ya está dando señales. <br />
            <span className="text-accent">PgGuardian te ayuda a escucharlas antes de que sea tarde.</span>
          </h2>
          <p className="text-lg text-sky/70 mb-10 max-w-2xl mx-auto">
            Menos incidentes, menos tiempo perdido, más visibilidad. Conecta tu base de datos hoy y obtén tu primer diagnóstico.
          </p>
          <button className="px-10 py-4 bg-accent text-white font-bold text-lg rounded-xl hover:bg-accent/90 transition shadow-2xl shadow-accent/30">
            Quiero probar PgGuardian
          </button>
          <p className="mt-4 text-sm text-sky/50">
            Sin instalación de agentes. Conexión read-only. Configuras en 5 minutos.
          </p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="bg-primary border-t border-primary/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7">
                <img src={logo} alt="PgGuardian" className="w-full h-full object-contain" />
              </div>
              <span className="text-sky font-semibold">PgGuardian</span>
            </div>
            <p className="text-sm text-sky/50">
              &copy; 2026 PgGuardian. Hecho en México para PyMEs mexicanas.
            </p>
          </div>
        </div>
      </footer>

    </div>
  )
}
