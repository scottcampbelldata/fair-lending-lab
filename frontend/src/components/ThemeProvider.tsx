"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

export type Theme = "light" | "dark";

interface ThemeCtx {
  theme: Theme;
  toggle: () => void;
  setTheme: (t: Theme) => void;
}

const Ctx = createContext<ThemeCtx | null>(null);

export const THEME_STORAGE_KEY = "flab-theme";

// Runs before paint (injected in <head>) so the document opens in the right
// theme — no flash of the wrong palette on load.
export const themeInitScript = `(function(){try{var t=localStorage.getItem('${THEME_STORAGE_KEY}');if(!t){t=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';}document.documentElement.dataset.theme=t;}catch(e){document.documentElement.dataset.theme='dark';}})();`;

function readDocTheme(): Theme {
  if (typeof document !== "undefined") {
    const attr = document.documentElement.dataset.theme;
    if (attr === "light" || attr === "dark") return attr;
  }
  return "dark";
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  // Deterministic initial value so the server render and the first client render
  // agree (no hydration mismatch). The pre-paint script has already applied the
  // real theme to the DOM via CSS variables; the effect below syncs React state
  // to it, which only affects JS-driven bits like the toggle icon and charts.
  const [theme, setThemeState] = useState<Theme>("dark");

  const apply = useCallback((t: Theme) => {
    document.documentElement.dataset.theme = t;
    try {
      localStorage.setItem(THEME_STORAGE_KEY, t);
    } catch {
      /* storage may be unavailable; the in-memory state still drives the UI */
    }
    setThemeState(t);
  }, []);

  // Keep state in sync with whatever the pre-paint script resolved.
  useEffect(() => {
    setThemeState(readDocTheme());
  }, []);

  const toggle = useCallback(
    () => apply(theme === "dark" ? "light" : "dark"),
    [theme, apply],
  );

  return (
    <Ctx.Provider value={{ theme, toggle, setTheme: apply }}>{children}</Ctx.Provider>
  );
}

export function useTheme(): ThemeCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}
