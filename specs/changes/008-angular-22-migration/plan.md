# Plan: 008-angular-22-migration

## Approach

We do not refactor. We bump. The implementation is:

1. Install Node 24 LTS via Homebrew (one-time, on the dev machine).
2. Create the SDD scaffolding (this change's spec / plan / tasks /
   context-pack, plus the `frontend-angular` and manifest updates).
3. Stash the SDD scaffolding so `ng update` sees a clean tree.
4. Run `ng update` per Angular's documented upgrade path, one major
   at a time (`@angular/cli@21`, `@angular/core@21`,
   `@angular/material@21`, `@angular/cdk@21`, then the same for
   `@22`). Each step rewrites `angular.json`, `package.json`, and
   `package-lock.json` automatically.
5. Re-pin the dependencies with `~` (replace the floating `^`
   introduced by `ng update` if it did) and verify the typecheck.
6. Validate the production build, the dev build, and the backend
   tests.
7. Smoke `ng serve`.
8. Restore the SDD scaffolding and update the manifest and
   contract.
9. Final consistency sweep.

Every `ng update`, `tsc`, `ng build`, and `ng serve` invocation
prepends `/opt/homebrew/opt/node@24/bin` to `PATH` so the v21 / v22
schematics pass their Node version gate.

## Steps

### Phase 0 — SDD + tooling

1. Install Node 24 LTS:

   ```bash
   brew install node@24
   /opt/homebrew/opt/node@24/bin/node --version
   ```

   Expectation: `v24.18.0` (or newer).

2. Create the change directory and write
   `specs/changes/008-angular-22-migration/{spec,plan,tasks,
   context-pack}.md`.
3. Update `specs/contracts/frontend-angular/contract.md`
   ("Angular 20" → "Angular 22").
4. Update `specs/manifest.yml` (add `008-angular-22-migration`,
   mark `007-angular-20-migration` as `superseded`, set `active:`
   to `008`).
5. Stash the SDD scaffolding:

   ```bash
   git stash push -u -m "008-angular-22-sdd-scaffold" -- \
       specs/contracts/frontend-angular/contract.md \
       specs/manifest.yml \
       specs/changes/008-angular-22-migration/
   ```

### Phase 1 — Major-by-major `ng update`

6. Bump to v21:

   ```bash
   PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
       npx ng update @angular/cli@21 @angular/core@21 \
       --allow-dirty --force
   ```

   Expectation: `package.json`, `package-lock.json`, and possibly
   `angular.json` are rewritten; `ng update` reports a clean
   apply.

7. Bump Material / CDK to v21:

   ```bash
   PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
       npx ng update @angular/material@21 @angular/cdk@21 \
       --allow-dirty --force
   ```

8. Bump to v22:

   ```bash
   PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
       npx ng update @angular/cli@22 @angular/core@22 \
       --allow-dirty --force
   ```

9. Bump Material / CDK to v22:

   ```bash
   PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
       npx ng update @angular/material@22 @angular/cdk@22 \
       --allow-dirty --force
   ```

10. After v22 lands, re-pin all `@angular/*`, `@angular/material`,
    `@angular/cdk`, `@angular/cli`, `@angular/build`,
    `@angular/compiler-cli`, `typescript`, and `zone.js` to `~`.

### Phase 2 — Material prebuilt sanity

11. Confirm `src/styles.css` and `angular.json` still import
    `@angular/material/prebuilt-themes/indigo-pink.css`. Material
    22 still ships the file but logs a deprecation; we keep it
    for the smallest possible diff. Document the deprecation in
    the contract's Configuration subsection if it is not already.

### Phase 3 — Validation

12. Typecheck:

    ```bash
    PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
        node_modules/.bin/tsc --noEmit -p tsconfig.app.json
    ```

    Expectation: exit 0. If a v22 deprecation in the framework
    forces a one-line change in `src/app/**/*.ts`, apply the
    smallest possible fix and document it in this plan as an
    "out-of-spec tweak".

13. Production build:

    ```bash
    PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
        node_modules/.bin/ng build --configuration production \
        --output-path /tmp/escalabirras-fe-prod
    ```

    Expectation: bundle produced.

14. Development build:

    ```bash
    PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
        node_modules/.bin/ng build --configuration development \
        --output-path /tmp/escalabirras-fe-dev
    ```

    Expectation: bundle produced, sourcemaps present.

15. Backend regression:

    ```bash
    /tmp/venv-002/bin/pytest backend -v
    ```

    Expectation: 64/64.

16. Manual smoke:

    ```bash
    PATH="/opt/homebrew/opt/node@24/bin:$PATH" \
        node_modules/.bin/ng serve --port 4200 &
    curl -s -o /tmp/index.html -w "HTTP %{http_code}\n" \
        http://localhost:4200/
    grep -q '<app-root>' /tmp/index.html
    ```

    Expectation: 200 + `<app-root>`.

### Phase 4 — Restore SDD and cleanup

17. Restore the SDD scaffolding:

    ```bash
    git stash pop
    ```

18. Verify the manifest and contract are coherent with the bump
    ("Angular 20" → "Angular 22", 007 superseded).

19. Resolve any `// TODO` markers left by `ng update`.

20. Final consistency sweep:

    ```bash
    grep -nR "Angular 20" specs/changes/008-angular-22-migration \
        specs/contracts/frontend-angular
    grep -nR "browserTarget" angular.json
    grep -nR "build-angular:browser" angular.json
    ```

    Expectation: no "Angular 20" mentions in the updated files;
    no `browserTarget`; no `:browser` builder.

## Risks

- **`ng update` peer dep failure on a transitive.** If a peer
  dep conflict is reported, we install with
  `--legacy-peer-deps` only as a last resort, after inspecting
  the conflict.
- **`ng update` non-idempotent.** Running `ng update` twice for
  the same major is safe but produces no-op diffs; we always run
  it once per major.
- **Schematic bugs.** `ng update` schematics occasionally miss
  an edge case. We treat any error as a blocker and resolve it
  before moving on.
- **v22 breaking changes outside our surface.** Detailed v22
  release notes are beyond the model's cutoff. We trust `ng
  update` schematics to apply any breaking-change rewrites in
  the codebase.
- **TypeScript bump.** Angular 22 may require TS 5.9.x. The
  current code is strict-mode-clean; the bump should be a
  no-op.
- **Builder config rename.** We trust `ng update` to perform
  any builder-option renames. If it does not, we do it
  manually.
- **Material 22 deprecation logs.** Expected and acceptable.
- **No frontend tests.** The migration is verified by
  typecheck, build, and manual smoke.
- **Disk space.** `npm install` for the two majors leaves two
  lockfiles in `node_modules/.angular/cache`. Acceptable.
- **Node PATH persistence.** Homebrew warns that `node@24` is
  keg-only and must be added to `~/.zshrc`. We do not modify
  the user's shell config (out of scope; documented as a
  recommendation in the context-pack).