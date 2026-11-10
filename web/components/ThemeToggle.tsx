"use client";

import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import { getTheme, setTheme, type Theme } from "@/lib/theme";

export default function ThemeToggle() {
  const [theme, set] = useState<Theme>("light");
  useEffect(() => set(getTheme()), []);
  const next: Theme = theme === "dark" ? "light" : "dark";
  return (
    <button
      className="iconbtn"
      aria-label={`Switch to ${next} mode`}
      onClick={() => { setTheme(next); set(next); }}
    >
      {theme === "dark" ? <Sun className="icon" aria-hidden /> : <Moon className="icon" aria-hidden />}
    </button>
  );
}
