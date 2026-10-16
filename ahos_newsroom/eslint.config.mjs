import next from 'eslint-config-next';

/** @type {import('eslint').Linter.Config[]} */
const config = [
  ...next,
  {
    ignores: ['.next/**', 'node_modules/**', 'screenshots/**', 'public/fonts/**'],
  },
];

export default config;
