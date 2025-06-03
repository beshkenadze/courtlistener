import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true, // Optional: to use Vitest globals like describe, it, expect without importing
    environment: 'node', // Or 'jsdom' if you need DOM APIs for some SDK tests
    include: ['sdk/courtlistener-api/**/*.test.ts'], // Pattern to find test files
    // setupFiles: ['./sdk/courtlistener-api/tests/setup.ts'], // Optional: for global test setup
  },
});
