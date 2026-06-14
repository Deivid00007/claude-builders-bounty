# CLAUDE.md - Next.js 15 + SQLite SaaS

Use this context for a greenfield SaaS app built with Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn/ui, Server Actions, and SQLite through `better-sqlite3` for local/single-node deployments or Turso/libSQL for hosted edge-friendly deployments.

## Stack & Versions

- Next.js 15 App Router with React Server Components by default because server-first pages keep data access close to routing and reduce client bundle size.
- TypeScript strict mode because SaaS billing, permissions, and account state need explicit types instead of runtime guesses.
- SQLite via `better-sqlite3` locally or Turso/libSQL in production because the schema stays portable while deployment can move from single-node to hosted without rewriting queries.
- Drizzle ORM for typed schema and migrations because handwritten SQL strings drift too easily from application types.
- Zod at every external boundary because form data, webhook payloads, and URL params are untrusted.
- Tailwind CSS plus shadcn/ui because components stay copy-editable and do not hide behavior behind a large design framework.
- Vitest for unit tests and Playwright for critical auth/billing flows because most SaaS failures are state transition bugs.

## Dev Commands

```bash
pnpm install
pnpm dev
pnpm lint
pnpm typecheck
pnpm test
pnpm test:e2e
pnpm db:generate
pnpm db:migrate
pnpm db:studio
```

Prefer `pnpm` for every command so lockfile behavior is consistent across local, CI, and deployment.

## Folder Structure

```text
app/
  (marketing)/
  (auth)/
  dashboard/
  api/
components/
  ui/
  forms/
  dashboard/
db/
  schema.ts
  migrations/
  client.ts
features/
  billing/
  organizations/
  projects/
  users/
lib/
  auth.ts
  env.ts
  errors.ts
  safe-action.ts
tests/
  unit/
  e2e/
```

- Put route segments in `app/` and product behavior in `features/` because App Router folders should explain navigation while feature folders explain business capability.
- Keep database schema in `db/schema.ts` and migrations in `db/migrations/` because schema ownership must be obvious during review.
- Put reusable primitives in `components/ui/`, composed product UI in `components/dashboard/`, and feature-specific forms in `components/forms/` because SaaS UIs otherwise become a single unsearchable component pile.
- Keep environment parsing in `lib/env.ts` because production secrets and local defaults must fail fast before a request handler runs.

## Naming Conventions

- Use kebab-case for route folders and files that map to URLs because paths should match what users and logs show.
- Use PascalCase for React components, camelCase for functions and variables, and snake_case for SQL columns because each layer keeps its native idiom.
- Name Server Actions as verbs ending in `Action`, such as `createProjectAction`, because call sites should reveal that a mutation crosses the server boundary.
- Name database tables plural nouns, such as `users`, `organizations`, and `invoices`, because joins and policies read naturally.
- Name foreign keys `<singular_table>_id`, such as `organization_id`, because it keeps SQL readable without ORM context.

## SQL & Migration Conventions

- Never edit an applied migration. Add a new migration because production databases must be reproducible from an empty file to current schema.
- Every migration must be reversible in principle: describe the rollback in the PR body even when the migration tool only applies forward changes, because data mistakes need an operational escape hatch.
- Add indexes with the query that needs them in the same PR because indexes without a caller are guesswork and callers without indexes become surprise latency.
- Use transactions for multi-table writes because account, membership, billing, and project state must move together.
- Store timestamps as ISO strings or integer milliseconds consistently; do not mix formats because sorting and retention jobs become incorrect.
- Prefer explicit SQL constraints for uniqueness and ownership invariants because UI checks are advisory and can be bypassed.
- Validate every dynamic value before it reaches SQL because SQLite is embedded, not harmless.

## Component Patterns

- Default to Server Components for reads because they can query data without exposing tokens or database clients to the browser.
- Use Client Components only for interactivity, browser APIs, optimistic UI, or controlled inputs because unnecessary client components increase hydration cost.
- Put data fetching in route-level Server Components or feature-level server modules, not inside generic UI components, because reusable UI should not own product queries.
- Use Server Actions for form mutations that belong to a page and route handlers for webhooks or external API clients because webhooks need raw request control.
- Return typed result objects from mutations: `{ ok: true, data }` or `{ ok: false, fieldErrors, formError }` because forms need predictable failure rendering.
- Keep loading, error, and empty states close to the route segment because SaaS dashboards are state-heavy and silent blank panels look broken.

## Auth, Tenancy, And Permissions

- Treat `organization_id` as part of every product query because SaaS bugs often leak cross-tenant data.
- Check permissions on the server, not in navigation or client components, because hidden buttons are not access control.
- Put role checks in `lib/auth.ts` or `features/*/permissions.ts` because scattered role strings rot quickly.
- Include `user_id`, `organization_id`, and request intent in audit logs for sensitive actions because support needs to explain billing and admin changes.

## Patterns To Follow

- Parse env vars once in `lib/env.ts` with Zod and export typed values because missing secrets should fail at boot.
- Add a unit test for every pure business rule and an e2e test for auth, onboarding, billing, and destructive flows because those paths lose money or trust when broken.
- Keep feature modules small: schema references, actions, queries, and components for one business concept should sit together because Claude Code can reason locally.
- Use explicit cache boundaries with `revalidatePath`, `revalidateTag`, or `unstable_noStore` because stale SaaS dashboards lead to duplicate actions and support tickets.
- Write PR notes with migration impact, auth impact, and test evidence because reviewers need operational context, not just file diffs.

## Anti-Patterns To Avoid

- Do not put `use client` at the top of whole route trees. It forces unnecessary browser execution and can leak server-only assumptions.
- Do not import database clients into Client Components. It breaks bundling and risks exposing server-only code.
- Do not mutate data in GET route handlers. Crawlers, prefetching, and retries can trigger unintended writes.
- Do not make nullable columns for required business state. Null-heavy SaaS data turns every query into implicit policy logic.
- Do not use raw `process.env` throughout the app. Scattered environment access hides missing configuration until runtime.
- Do not skip migrations for "small" schema tweaks. Local drift is exactly how production deploys fail.
- Do not hide authorization in UI state. It gives a false sense of security and fails on direct requests.

## Claude Code Working Rules

- Before editing, inspect `package.json`, `db/schema.ts`, and the target route or feature folder because the app's conventions matter more than generic Next.js advice.
- When adding a feature, create or update schema, query, action, UI, validation, and tests in one coherent change because partial SaaS features are hard to safely resume.
- When touching migrations, summarize data impact and rollback expectations in the final response because schema changes are operational work.
- When uncertain about product behavior, prefer a narrow server-side implementation with explicit TODO comments over adding broad abstractions because premature frameworks slow small SaaS teams.
- After changes, run `pnpm lint`, `pnpm typecheck`, and the narrowest relevant tests because TypeScript alone does not prove auth or data flow behavior.
