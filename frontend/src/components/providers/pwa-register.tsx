"use client";

/**
 * Registers the service worker so the site can be installed on phones.
 */

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    const basePath = process.env.NEXT_PUBLIC_BASE_PATH || "";
    const swUrl = `${basePath}/sw.js`;
    const scope = `${basePath}/` || "/";

    navigator.serviceWorker.register(swUrl, { scope }).catch(() => {
      // Manifest still enables Add to Home Screen / Install app.
    });
  }, []);

  return null;
}
