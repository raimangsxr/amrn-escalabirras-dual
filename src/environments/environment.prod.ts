/**
 * Production environment overrides.
 *
 * The Angular build replaces this file at build time via
 * `angular.json` -> `fileReplacements`. Before deploying:
 *
 *   1. Set `apiBaseUrl` to the public origin of the FastAPI
 *      backend (e.g. `https://api.example.com/v1`). Do NOT include a
 *      trailing slash.
 *   2. Confirm `embedTokenQueryParam`, `loginPath`, and
 *      `sessionStorageKey` still match the backend contract.
 *
 * The CI pipeline should assert that `apiBaseUrl` is non-empty
 * before merging to main.
 */
export const environment = {
  apiBaseUrl: 'REPLACE_AT_BUILD_TIME',
  celebrationDurationMs: 12000,
  loginPath: '/login',
  embedTokenQueryParam: 'embed_token',
  sessionStorageKey: 'escalabirras.session',
};