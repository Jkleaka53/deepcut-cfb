export default function WhatIfBanner({ text, canReset, onReset }: { text: string; canReset: boolean; onReset: () => void }) {
  return (
    <div className="whatif" role="status">
      <span>{text}</span>
      <span className="whatif-actions">
        <a href="#availability" onClick={() => document.querySelectorAll<HTMLDetailsElement>(".aw-group").forEach((d) => { d.open = true; })}>Change</a>
        {canReset && <button type="button" onClick={onReset}>Reset to defaults</button>}
      </span>
    </div>
  );
}
