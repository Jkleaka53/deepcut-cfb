export type Theme = "light" | "dark";
export const THEME_KEY = "cfbm:theme";

export function getTheme(): Theme {
  try {
    return localStorage.getItem(THEME_KEY) === "dark" ? "dark" : "light";
  } catch {
    return "light";
  }
}

export function setTheme(t: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, t);
  } catch {
    // Storage blocked (private mode etc.): the switch still works for this page view.
  }
  if (typeof document !== "undefined") document.documentElement.dataset.theme = t;
}

/** Inline <head> script: apply a stored dark choice before first paint. Default stays light. */
export const THEME_BOOT = `try{if(localStorage.getItem("${THEME_KEY}")==="dark")document.documentElement.dataset.theme="dark"}catch(e){}`;
