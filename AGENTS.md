# escalabirras Agent Instructions

## SDD policy

1. Start every SDD task from `specs/manifest.yml`. The manifest's
   `active:` block names the active change, contract, and context
   pack; treat them as the source of truth.
2. Do not scan all specs by default. Only read the active contract
   and the active context pack for the change you are working on.
3. Treat `specs/contracts/**/contract.md` (live contracts) as the
   authoritative description of current behavior.
4. Treat `specs/changes/**` as incremental records. Earlier changes
   describe what already shipped.
5. Do not read `specs/archive/**` unless explicitly justified.
6. If behavior changes, update the affected active contract before
   implementation (rule 7 in the bootstrap checklist).
7. Keep `specs/manifest.yml` synchronized with new contracts, moved
   paths, and change status. When a change closes, mark it
   `superseded` in the manifest and (if applicable) archive its
   contract to `specs/archive/`.
8. Run narrow tests first, then broader validation.

## Active SDD work

The single source of truth is `specs/manifest.yml`. At the time of
writing, it points at:

- Active change: `specs/changes/004-auth-and-embed-tokens/`
- Active contract: `specs/contracts/auth/contract.md`
- Context pack: `specs/changes/004-auth-and-embed-tokens/context-pack.md`

Other live contracts (also documented in `specs/manifest.yml`):
`api-rest`, `persistence-postgres`, `frontend-angular`. The
`app-core` contract is archived at `specs/archive/app-core/`.

## Suggested flow

`specify -> clarify -> checklist -> plan -> tasks -> analyze -> implement`

When in doubt, read `specs/manifest.yml` first; do not trust older
notes that may predate recent changes.
