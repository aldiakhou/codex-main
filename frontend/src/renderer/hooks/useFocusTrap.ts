import { useEffect, useRef } from 'react';

/**
 * Accessibility: trap focus inside a container while open and restore focus on close.
 * - Adds keydown handler for Tab cycling and Escape to close.
 * - Focuses the first focusable element on mount; restores the previously focused element on unmount.
 */
export function useFocusTrap<T extends HTMLElement>(
  isOpen: boolean,
  onClose?: () => void
) {
  const containerRef = useRef<T | null>(null);
  const prevFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    prevFocusRef.current = (document.activeElement as HTMLElement) || null;

    // Focus the first focusable element or container
    const focusFirst = () => {
      const el = containerRef.current;
      if (!el) return;
      const focusables = el.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
      );
      if (focusables.length > 0) {
        focusables[0].focus();
      } else {
        el.focus();
      }
    };
    const tid = window.setTimeout(focusFirst, 0);

    const onKeyDown = (e: KeyboardEvent) => {
      const el = containerRef.current;
      if (!el) return;
      if (e.key === 'Escape') {
        onClose?.();
        e.stopPropagation();
        return;
      }
      if (e.key === 'Tab') {
        const focusables = Array.from(
          el.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])'
          )
        ).filter((n) => n.offsetParent !== null || n === document.activeElement);
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        const active = document.activeElement as HTMLElement | null;
        if (e.shiftKey) {
          if (active === first || !el.contains(active)) {
            last.focus();
            e.preventDefault();
          }
        } else {
          if (active === last) {
            first.focus();
            e.preventDefault();
          }
        }
      }
    };
    document.addEventListener('keydown', onKeyDown, true);

    return () => {
      window.clearTimeout(tid);
      document.removeEventListener('keydown', onKeyDown, true);
      // Restore previous focus
      prevFocusRef.current?.focus?.();
    };
  }, [isOpen, onClose]);

  return { containerRef } as const;
}
