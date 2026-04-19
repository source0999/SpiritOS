"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

type OverlayLockValue = {
  mainLocked: boolean;
  setNavDrawerOpen: (open: boolean) => void;
  setCommandBarOpen: (open: boolean) => void;
};

const OverlayLockContext = createContext<OverlayLockValue | null>(null);

export function OverlayLockProvider({ children }: { children: ReactNode }) {
  const [navOpen, setNavOpen] = useState(false);
  const [commandOpen, setCommandOpen] = useState(false);

  const setNavDrawerOpen = useCallback((open: boolean) => {
    setNavOpen(open);
  }, []);

  const setCommandBarOpen = useCallback((open: boolean) => {
    setCommandOpen(open);
  }, []);

  const mainLocked = navOpen || commandOpen;

  const value = useMemo(
    () => ({
      mainLocked,
      setNavDrawerOpen,
      setCommandBarOpen,
    }),
    [mainLocked, setNavDrawerOpen, setCommandBarOpen],
  );

  return (
    <OverlayLockContext.Provider value={value}>
      {children}
    </OverlayLockContext.Provider>
  );
}

export function useOverlayLock(): OverlayLockValue {
  const ctx = useContext(OverlayLockContext);
  if (!ctx) {
    throw new Error("useOverlayLock must be used within OverlayLockProvider");
  }
  return ctx;
}
