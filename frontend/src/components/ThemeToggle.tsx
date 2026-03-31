"use client";

import { Sun, Moon } from "lucide-react";
import { useTheme } from "./ThemeContext";
import { useEffect, useState } from "react";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return <div style={{ width: '40px', height: '40px' }} />;

  return (
    <button
      onClick={toggleTheme}
      style={{
        width: '40px',
        height: '40px',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        backgroundColor: 'var(--bg-tertiary)',
        border: '1px solid var(--border-color)',
        color: 'var(--text-primary)',
        transition: 'all 0.2s ease',
        boxShadow: 'var(--shadow-sm)'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--brand-500)';
        e.currentTarget.style.backgroundColor = 'var(--brand-50)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border-color)';
        e.currentTarget.style.backgroundColor = 'var(--bg-tertiary)';
      }}
      title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
    >
      {theme === "light" ? (
        <Moon size={20} className="text-secondary" />
      ) : (
        <Sun size={20} className="text-brand" />
      )}
    </button>
  );
}
