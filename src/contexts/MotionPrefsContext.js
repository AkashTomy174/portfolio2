import { createContext, useContext } from 'react';

export const MotionPrefsContext = createContext(false);
export const useReducedMotion = () => useContext(MotionPrefsContext);
