import { useEffect, useCallback } from 'react';

type KeyHandler = (e: KeyboardEvent) => void;

interface ShortcutMap {
  [key: string]: KeyHandler;
}

function isInputFocused(): boolean {
  const tag = document.activeElement?.tagName?.toLowerCase();
  return tag === 'input' || tag === 'textarea' || tag === 'select';
}

export function useKeyboardShortcuts(shortcuts: ShortcutMap, deps: unknown[] = []) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Build key string
      const parts: string[] = [];
      if (e.ctrlKey || e.metaKey) parts.push('mod');
      if (e.shiftKey) parts.push('shift');
      if (e.altKey) parts.push('alt');
      parts.push(e.key.toLowerCase());
      const keyCombo = parts.join('+');

      const handler = shortcuts[keyCombo] || shortcuts[e.key.toLowerCase()];
      if (!handler) return;

      // Allow mod+ shortcuts even in inputs (like Ctrl+K)
      if (isInputFocused() && !e.ctrlKey && !e.metaKey) return;

      e.preventDefault();
      handler(e);
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [shortcuts, ...deps],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
