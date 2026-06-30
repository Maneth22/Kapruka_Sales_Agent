import { createTheme } from '@mantine/core';

export const theme = createTheme({
  primaryColor: 'deepPurple',
  colors: {
    deepPurple: [
      '#f3eff9', '#e0d6f0', '#cbb8e5', '#b399d8', '#9c7acc',
      '#8549c9', '#6a3ba3', '#432a72', '#321f55', '#211438',
    ],
  },
  primaryShade: 7,
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  headings: { fontFamily: 'inherit' },
});
