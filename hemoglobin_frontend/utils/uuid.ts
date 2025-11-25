/**
 * Cross-platform UUID generator
 * Works in both browser and React Native environments
 */
export function generateUUID(): string {
  // Try to use crypto.randomUUID() if available (modern browsers/Node.js)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  // Fallback: Generate UUID v4 manually (for React Native and older environments)
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

