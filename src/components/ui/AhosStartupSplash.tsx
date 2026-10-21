"use client";

import { useEffect, useState } from "react";
import { LionSunMark } from "./Brand";

const storageKey = "ahos.startup.seen.v1";

function shouldShowStartupSplash(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return sessionStorage.getItem(storageKey) !== "1";
  } catch {
    return false;
  }
}

export function AhosStartupSplash() {
  const [visible, setVisible] = useState(shouldShowStartupSplash);

  useEffect(() => {
    if (!visible) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const hide = () => {
      setVisible(false);
      try {
        sessionStorage.setItem(storageKey, "1");
      } catch {
        /* optional */
      }
    };

    if (document.readyState === "complete") {
      window.setTimeout(hide, reduced ? 120 : 380);
    } else {
      window.addEventListener("load", () => window.setTimeout(hide, reduced ? 80 : 280), {
        once: true,
      });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="ah-startup-splash" role="status" aria-live="polite">
      <div className="ah-startup-splash-inner">
        <div className="ah-startup-lockup">
          <LionSunMark variant="splash" decorative={false} />
          <span className="ah-startup-wordmark">AHOS</span>
        </div>
        <span className="ah-startup-tagline">CONNECTED INTELLIGENCE</span>
      </div>
    </div>
  );
}
