"use client";

interface Chip { value: string; label: string; icon?: React.ReactNode }

export default function ChipRow({ chips, value, onChange, label, className = "" }:
  { chips: Chip[]; value: string; onChange: (v: string) => void; label: string; className?: string }) {
  return (
    <div className="chiprow" role="group" aria-label={label}>
      {chips.map((c) => (
        <button key={c.value} className={`chip ${className} ${c.value === value ? "on" : ""}`} aria-pressed={c.value === value}
          onClick={() => onChange(c.value)}>
          {c.icon}{c.label}
        </button>
      ))}
    </div>
  );
}
