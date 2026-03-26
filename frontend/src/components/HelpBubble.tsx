import { useState, useRef, useEffect } from 'react';
import type { ReactNode } from 'react';

interface Props {
  title: string;
  children: ReactNode;
}

export default function HelpBubble({ title, children }: Props) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open]);

  return (
    <div ref={ref} className="relative inline-flex">
      <button
        onClick={() => setOpen(!open)}
        className="w-4 h-4 rounded-full flex items-center justify-center text-xs leading-none"
        style={{
          background: 'var(--bg-tertiary)',
          color: open ? 'var(--accent)' : 'var(--text-secondary)',
          border: '1px solid var(--border)',
          fontSize: '10px',
          cursor: 'pointer',
        }}
        title="Help"
      >
        ?
      </button>

      {open && (
        <div
          className="absolute z-50 rounded-lg p-3"
          style={{
            top: '100%',
            left: '50%',
            transform: 'translateX(-50%)',
            marginTop: '6px',
            width: '260px',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            boxShadow: '0 8px 24px rgba(0,0,0,0.4)',
          }}
        >
          <div className="text-xs font-bold mb-1.5" style={{ color: 'var(--accent)' }}>
            {title}
          </div>
          <div className="text-xs leading-relaxed" style={{ color: 'var(--text-primary)' }}>
            {children}
          </div>
        </div>
      )}
    </div>
  );
}
