"use client";

import { useCallback, useEffect, useRef } from "react";

export function useAdminScrollRestore(dependencyKey: string) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const savedScrollTop = useRef(0);
  const shouldRestore = useRef(false);

  const saveScroll = useCallback(() => {
    if (scrollRef.current) {
      savedScrollTop.current = scrollRef.current.scrollTop;
    }
  }, []);

  const requestRestore = useCallback(() => {
    shouldRestore.current = true;
  }, []);

  const restoreScroll = useCallback(() => {
    if (!shouldRestore.current || !scrollRef.current) return;
    scrollRef.current.scrollTop = savedScrollTop.current;
    shouldRestore.current = false;
  }, []);

  useEffect(() => {
    if (!shouldRestore.current) return;
    requestAnimationFrame(() => {
      restoreScroll();
    });
  }, [dependencyKey, restoreScroll]);

  return { scrollRef, saveScroll, requestRestore, restoreScroll };
}
