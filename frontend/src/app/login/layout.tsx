export default function AuthLayout({
    children,
  }: {
    children: React.ReactNode
  }) {
    return (
      <div className="auth-wrapper animate-fade-in">
        <div style={{ position: 'absolute', top: '10%', right: '10%', width: '400px', height: '400px', borderRadius: '50%', background: 'var(--brand-500)', opacity: 0.1, filter: 'blur(100px)', zIndex: 0 }}></div>
        <div style={{ position: 'absolute', bottom: '10%', left: '10%', width: '600px', height: '600px', borderRadius: '50%', background: 'var(--brand-600)', opacity: 0.15, filter: 'blur(150px)', zIndex: 0 }}></div>
        
        <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: '440px', padding: '1rem' }}>
          {children}
        </div>
      </div>
    )
  }
