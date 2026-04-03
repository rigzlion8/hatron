"use client";

import { Plus } from 'lucide-react';

interface Product {
  id: string;
  name: string;
  price: number;
  category_name?: string;
  image_url?: string;
}

interface ProductCardProps {
  product: Product;
  onAdd: (product: Product) => void;
}

export default function ProductCard({ product, onAdd }: ProductCardProps) {
  const formatKES = (amount: number) => {
    return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div 
      className="card animate-fade-in"
      style={{
        padding: '0',
        display: 'flex',
        flexDirection: 'column',
        cursor: 'pointer',
        transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        border: '1px solid var(--border-color)',
        backgroundColor: 'var(--bg-primary)',
        overflow: 'hidden',
        height: '100%'
      }}
      onClick={() => onAdd(product)}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--accent-primary)';
        e.currentTarget.style.transform = 'translateY(-4px)';
        e.currentTarget.style.boxShadow = '0 12px 24px -10px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-color)';
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      {/* Product Image */}
      <div style={{
        width: '100%',
        height: '130px',
        backgroundColor: 'var(--bg-tertiary)',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.25rem',
        flexShrink: 0
      }}>
        {product.image_url ? (
          <img 
            src={product.image_url} 
            alt={product.name}
            style={{
              maxWidth: '100%',
              maxHeight: '100%',
              objectFit: 'contain'
            }}
          />
        ) : (
          <div style={{ color: 'var(--text-tertiary)', opacity: 0.3 }}>
            <Plus size={40} strokeWidth={1} />
          </div>
        )}
      </div>

      <div style={{ padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1 }}>
        <div style={{
          fontSize: '0.7rem',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--text-tertiary)',
          fontWeight: 600
        }}>
          {product.category_name || 'General'}
        </div>
        
        <div style={{ 
          fontWeight: 600, 
          fontSize: '0.95rem',
          color: 'var(--text-primary)',
          lineHeight: 1.4
        }}>
          {product.name}
        </div>
        
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginTop: 'auto',
          gap: '0.5rem'
        }}>
          <div style={{ 
            fontSize: '1rem', 
            fontWeight: 700, 
            color: 'var(--accent-primary)',
            lineHeight: 1.2
          }}>
            {formatKES(product.price)}
          </div>
          
          <div style={{
            width: '28px',
            height: '28px',
            borderRadius: '50%',
            backgroundColor: 'var(--bg-tertiary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-secondary)',
            flexShrink: 0
          }}>
            <Plus size={16} />
          </div>
        </div>
      </div>
    </div>
  );
}
