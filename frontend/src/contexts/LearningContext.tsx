import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

interface LearningState {
  learningMode: boolean;
  hasSeenOnboarding: boolean;
  toggleLearningMode: () => void;
  markOnboardingComplete: () => void;
}

const LearningContext = createContext<LearningState | null>(null);

const STORAGE_KEY_MODE = 'quantumlens_learningMode';
const STORAGE_KEY_ONBOARDING = 'quantumlens_hasSeenOnboarding';

function readBool(key: string, fallback: boolean): boolean {
  try {
    const v = localStorage.getItem(key);
    if (v === null) return fallback;
    return v === 'true';
  } catch {
    return fallback;
  }
}

export function LearningProvider({ children }: { children: ReactNode }) {
  const [hasSeenOnboarding, setHasSeenOnboarding] = useState(() => readBool(STORAGE_KEY_ONBOARDING, false));
  const [learningMode, setLearningMode] = useState(() => {
    // Default to ON for first-time users, respect saved preference otherwise
    const seen = readBool(STORAGE_KEY_ONBOARDING, false);
    return seen ? readBool(STORAGE_KEY_MODE, true) : true;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_MODE, String(learningMode));
  }, [learningMode]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY_ONBOARDING, String(hasSeenOnboarding));
  }, [hasSeenOnboarding]);

  const toggleLearningMode = () => setLearningMode(prev => !prev);
  const markOnboardingComplete = () => setHasSeenOnboarding(true);

  return (
    <LearningContext value={{ learningMode, hasSeenOnboarding, toggleLearningMode, markOnboardingComplete }}>
      {children}
    </LearningContext>
  );
}

export function useLearning(): LearningState {
  const ctx = useContext(LearningContext);
  if (!ctx) throw new Error('useLearning must be used within LearningProvider');
  return ctx;
}
