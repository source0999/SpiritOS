"use client";

// ── `/chat` mobile chrome only — dock hide + shell padding react to composer / keyboard ─
// > Dashboard home mounts WorkspacePrimarySidebar without this provider; hooks return null.
import {
  createContext,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";

export type SpiritWorkspaceMobileChromeValue = {
  composerFocused: boolean;
  setComposerFocused: Dispatch<SetStateAction<boolean>>;
  /** Latest keyboard inset (px) from visualViewport; driven by parent shell hook. */
  keyboardInsetPx: number;
};

const SpiritWorkspaceMobileChromeContext =
  createContext<SpiritWorkspaceMobileChromeValue | null>(null);

export function useSpiritWorkspaceMobileChrome(): SpiritWorkspaceMobileChromeValue | null {
  return useContext(SpiritWorkspaceMobileChromeContext);
}

export function SpiritWorkspaceMobileChromeProvider({
  children,
  keyboardInsetPx,
}: {
  children: ReactNode;
  keyboardInsetPx: number;
}) {
  const [composerFocused, setComposerFocused] = useState(false);
  const value = useMemo(
    () => ({ composerFocused, setComposerFocused, keyboardInsetPx }),
    [composerFocused, keyboardInsetPx],
  );
  return (
    <SpiritWorkspaceMobileChromeContext.Provider value={value}>
      {children}
    </SpiritWorkspaceMobileChromeContext.Provider>
  );
}
