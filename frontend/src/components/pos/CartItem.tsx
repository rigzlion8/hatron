"use client";

import { Minus, Plus, Trash2 } from 'lucide-react';

interface CartItemData {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartItemProps {
  item: CartItemData;
  onUpdateQuantity: (id: string, delta: number) => void;
  onRemove: (id: string) => void;
}

export default function CartItem({ item, onUpdateQuantity, onRemove }: CartItemProps) {
  const formatKES = (amount: number) => {
    return `KES ${amount.toLocaleString('en-KE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <div 
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        padding: '1rem',
        borderBottom: '1px solid var(--border-color)',
        transition: 'all 0.2s ease'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ 
          fontWeight: 600, 
          fontSize: '0.95rem',
          color: 'var(--text-primary)',
          flexGrow: 1
        }}>
          {item.name}
        </div>
        <button 
          onClick={() => onRemove(item.id)}
          style={{ 
            background: 'none', 
            border: 'none', 
            color: 'var(--text-tertiary)',
            cursor: 'pointer',
            padding: '4px'
          }}
        >
          <Trash2 size={16} />
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ 
          fontSize: '0.85rem', 
          color: 'var(--text-secondary)',
          fontWeight: 500
        }}>
          {formatKES(item.price)} x {item.quantity}
        </div>
        
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.25rem',
          backgroundColor: 'var(--bg-tertiary)',
          padding: '4px',
          borderRadius: '4px'
        }}>
          <button 
            onClick={() => onUpdateQuantity(item.id, -1)}
            style={{ 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex',
              padding: '4px'
            }}
          >
            <Minus size={14} />
          </button>
          <span style={{ 
            fontSize: '0.85rem', 
            fontWeight: 700, 
            minWidth: '20px', 
            textAlign: 'center' 
          }}>
            {item.quantity}
          </span>
          <button 
            onClick={() => onUpdateQuantity(item.id, 1)}
            style={{ 
              background: 'none', 
              border: 'none', 
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              display: 'flex',
              padding: '4px'
            }}
          >
            <Plus size={14} />
          </button>
        </div>
        
        <div style={{ 
          fontWeight: 700, 
          color: 'var(--text-primary)',
          fontSize: '0.95rem'
        }}>
          {formatKES(item.price * item.quantity)}
        </div>
      </div>
    </div>
  );
}
