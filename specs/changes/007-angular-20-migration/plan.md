# Plan: 007-angular-20-migration

## Approach

We do not refactor. We bump. The implementation is:

1. Run `ng update` per Angular's documented upgrade path (one major
   at a time, with `ng update @angular/cli@N @angular/core@N` for
   `N = 17, 18, 19, 20`). Each step rewrites `angular.json`,
   `package.json`, and `package-lock.json` automatically.
2. After the four `ng update` passes land, we re-pin the
   dependencies with `~` (replace the floating `^` introduced by
   `ng update` if it did) and add the test builder.
3. Verify the typecheck, the dev build, the production build, and
   the backend tests.
4. Update the contract and the manifest.
5. Smoke `ng serve`.

Why incremental `ng update`? `ng update` ships schematics that
rewrite `angular.json` to the new builder names, drop deprecated
options, and bump peer deps. Skipping a major is supported by the
Angular CLI but is officially discouraged because the schematics
contain per-major transformations (e.g. v17 introduces the
`application` builder; v18 removes `ngcc`; v19 standardizes the
test builder; v20 raises the minimum Node). Running one major at
a time is the canonical path.

## Steps

### Phase 0 — SDD

1. Write `specs/changes/007-angular-20-migration/spec.md`.
2. Write this plan.
3. Write `tasks.md`.
4. Write `context-pack.md`.
5. Update `specs/contracts/frontend-angular/contract.md`
   ("Angular 16" → "Angular 20").
6. Update `specs/manifest.yml` (add `007-angular-20-migration`,
   set `active:` block).

### Phase 1 — Major-by-major `ng update`

7. Pre-flight:

   ```bash
   node --version  # must be >= 18.13 to start; >= 20.11 by v20
   npm --version
   git status     # clean working tree before the upgrade
   ```

8. Bump to v17:

   ```bash
   npx ng update @angular/cli@17 @angular/core@17 \
       @angular/material@17 @angular/cdk@17
   ```

   Expectation: `package.json`, `package-lock.json`, and
   `angular.json` are rewritten; `ng update` reports a clean
   apply.

9. Bump to v18:

   ```bash
   npx ng update @angular/cli@18 @angular/core@18 \
       @angular/material@18 @angular/cdk@18
   ```

10. Bump to v19:

    ```bash
    npx ng update @angular/cli@19 @angular/core@19 \
        @angular/material@19 @angular/cdk@19
    ```

11. Bump to v20:

    ```bash
    npx ng update @angular/cli@20 @angular/core@20 \
        @angular/material@20 @angular/cdk@20
    ```

12. After v20 lands, re-pin all `@angular/*`, `@angular/material`,
    `@angular/cdk`, `@angular-devkit/build-angular` (or
    `@angular/build`), `typescript`, `zone.js` to `~` to keep the
    contract with the rest of the project (which already uses
    `~`).

### Phase 2 — Material prebuilt sanity

13. Confirm `src/styles.css` and `angular.json` still import
    `@angular/material/prebuilt-themes/indigo-pink.css`. Material
    20 still ships the file but logs a deprecation; we keep it for
    the smallest possible diff. Document the deprecation in the
    contract's Configuration subsection.

14. If `ng update` rewrote `src/styles.css` to remove the prebuilt
    import, restore it from the template (or accept the M3 rewrite
    if `ng update` left a working M3 theme block). Either way,
    the bundle must look correct.

### Phase 3 — Validation

15. Typecheck:

    ```bash
    node_modules/.bin/tsc --noEmit -p tsconfig.app.json
    ```

    Expectation: exit 0. If a v20 deprecation in the framework
    forces a one-line change in `src/app/**/*.ts`, apply the
    smallest possible fix and document it in this plan as an
    "out-of-spec tweak".

16. Production build:

    ```bash
    node_modules/.bin/ng build --configuration production \
        --output-path /tmp/escalabirras-fe-prod
    ```

    Expectation: bundle produced.

17. Development build:

    ```bash
    node_modules/.bin/ng build --configuration development \
        --output-path /tmp/escalabirras-fe-dev
    ```

    Expectation: bundle produced, sourcemaps present.

18. Backend regression:

    ```bash
    /tmp/venv-002/bin/pytest backend -v
    ```

    Expectation: 64/64.

19. Manual smoke:

    ```bash
    node_modules/.bin/ng serve --port 4200 &
    curl -s -o /tmp/index.html -w "HTTP %{http_code}\n" \
        http://localhost:4200/
    grep -q '<app-root>' /tmp/index.html
    ```

    Expectation: 200 + `<app-root>`.

### Phase 4 — Cleanup

20. If `ng update` left any `// TODO` markers in the migrated
    files, resolve them now.

21. Final consistency sweep:

    ```bash
    grep -nR "Angular 16" specs/changes/007-angular-20-migration \
        specs/contracts/frontend-angular
    grep -nR "browserTarget" angular.json
    grep -nR "build-angular:browser" angular.json
    ```

    Expectation: no "Angular 16" mentions in the updated files;
    no `browserTarget`; no `:browser` builder.

22. Update `specs/manifest.yml` to mark
    `007-angular-20-migration` as `superseded` (because the active
    work will move to the next change after this one closes).

## Risks

- **`ng update` peer dep failure on a transitive.** If a peer
  dep conflict is reported, we install with
  `--legacy-peer-deps` only as a last resort, after inspecting
  the conflict.
- **`ng update` non-idempotent.** Running `ng update` twice for the
  same major is safe but produces no-op diffs; we always run it
  once per major.
- **Schematic bugs.** `ng update` schematics occasionally miss an
  edge case (e.g. a custom `karma.conf.js`). We treat any error as
  a blocker and resolve it before moving on.
- **TypeScript 5.8 strict mode.** Same as `005`: existing code is
  strict-clean; the bump should be a no-op for our templates and
  services. If a new error appears, fix it as the smallest
  possible change.
- **Builder config rename.** We trust `ng update` to perform the
  `browserTarget` → `buildTarget` rename. If it does not, we do it
  manually.
- **Material 20 deprecation logs.** Expected and acceptable.
- **No frontend tests.** The migration is verified by typecheck,
  build, and manual smoke. Documented as an existing constraint.
- **Disk space.** `npm install` for the four majors leaves four
  lockfiles in `node_modules/.angular/cache`. Acceptable.