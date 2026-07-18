# RealDoor — Frontend

Next.js 16 + React 19 web client for the RealDoor application-readiness copilot.
Drives the three-stage renter journey: **Profile → Understand → Prepare**. See the
[root README](../README.md) for the full challenge brief.

> **Note:** This is Next.js 16 (App Router). APIs and conventions differ from older
> versions — see `AGENTS.md`. Check `node_modules/next/dist/docs/` before writing code.

## What lives here

| Path | Purpose |
|---|---|
| `src/app/` | App Router pages, layouts, and global styles (`page.tsx`, `layout.tsx`, `globals.css`). |
| `public/` | Static assets served as-is. |
| `next.config.ts` | Next.js configuration. |
| `eslint.config.mjs` | ESLint (flat config, `eslint-config-next`). |
| `postcss.config.mjs` | PostCSS for Tailwind CSS v4. |
| `tsconfig.json` | TypeScript configuration. |
| `AGENTS.md` / `CLAUDE.md` | Agent guidance for this Next.js version. |

### Stack

- **Next.js 16** (App Router) + **React 19**
- **TypeScript 5**
- **Tailwind CSS v4**
- **ESLint 9**

## Setup

Requires **Node.js 20+**.

```bash
cd frontend
npm install
```

## Run

```bash
npm run dev
```

Open http://localhost:3000. Pages hot-reload on edit; start with `src/app/page.tsx`.

The frontend talks to the backend API (default http://localhost:8000) — start the
[backend](../backend/README.md) too for a working end-to-end flow.

## Scripts

| Command | Does |
|---|---|
| `npm run dev` | Start the dev server. |
| `npm run build` | Production build. |
| `npm run start` | Serve the production build. |
| `npm run lint` | Run ESLint. |
