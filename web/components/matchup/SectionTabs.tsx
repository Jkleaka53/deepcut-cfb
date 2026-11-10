"use client";

import { useEffect, useState } from "react";

export const TABS = [
  { id: "preview", label: "Preview" }, { id: "passing", label: "Passing game" },
  { id: "qb", label: "QB splits" }, { id: "availability", label: "Availability" },
];

export default function SectionTabs() {
  const [active, setActive] = useState("preview");
  useEffect(() => {
    const onScroll = () => {
      const bar = document.querySelector(".tabs")?.getBoundingClientRect().bottom ?? 0;
      let cur = TABS[0].id;
      for (const t of TABS) {
        const el = document.getElementById(t.id);
        if (el && el.getBoundingClientRect().top <= bar + 4) cur = t.id;
      }
      setActive(cur);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (
    <nav className="tabs" aria-label="Sections">
      {TABS.map((t) => (
        <a key={t.id} href={`#${t.id}`} className={active === t.id ? "on" : ""} aria-current={active === t.id ? "true" : undefined}
          onClick={(e) => { e.preventDefault(); document.getElementById(t.id)?.scrollIntoView({ behavior: "auto" }); setActive(t.id); }}>
          {t.label}
        </a>
      ))}
    </nav>
  );
}
