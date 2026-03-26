import { useState, useCallback } from 'react';

interface UndoRedoState<T> {
  history: T[];
  index: number;
}

export function useUndoRedo<T>(initial: T) {
  const [state, setState] = useState<UndoRedoState<T>>({
    history: [initial],
    index: 0,
  });

  const current = state.history[state.index];
  const canUndo = state.index > 0;
  const canRedo = state.index < state.history.length - 1;

  const set = useCallback((value: T) => {
    setState(prev => {
      const newHistory = prev.history.slice(0, prev.index + 1);
      newHistory.push(value);
      // Cap history at 50 entries
      if (newHistory.length > 50) newHistory.shift();
      return { history: newHistory, index: newHistory.length - 1 };
    });
  }, []);

  const undo = useCallback(() => {
    setState(prev => prev.index > 0
      ? { ...prev, index: prev.index - 1 }
      : prev
    );
  }, []);

  const redo = useCallback(() => {
    setState(prev => prev.index < prev.history.length - 1
      ? { ...prev, index: prev.index + 1 }
      : prev
    );
  }, []);

  // Reset history (e.g., when loading a preset)
  const reset = useCallback((value: T) => {
    setState({ history: [value], index: 0 });
  }, []);

  return { current, set, undo, redo, reset, canUndo, canRedo };
}
