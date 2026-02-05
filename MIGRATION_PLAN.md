# Next.js Migration Plan - Create React App → Next.js 15 (App Router)

## Overview
Migrating from Create React App (deprecated) to Next.js 15 with App Router.

**Timeline:** 1-2 days
**Risk Level:** Low (mostly file structure changes)
**Regression Risk:** Minimal (API calls unchanged)

---

## Current State

### Existing Files
```
frontend/
  src/
    App.js (main component)
    App.css
    index.js (entry point)
    index.css
    components/
      FileUpload.js + .css
      PlayerConfig.js + .css
      ArrangementDisplay.js + .css
    (test files - will remove)
  public/
  package.json (CRA + react-scripts)
```

### Dependencies to Migrate
- react: 19.2.4 ✅
- react-dom: 19.2.4 ✅
- axios: 1.6.0 ✅
- react-scripts: 5.0.1 ❌ (REMOVE)
- @testing-library/* (optional - can remove)

---

## Migration Strategy

### Phase 1: Backup & Create New Next.js Project
1. Backup current frontend directory
2. Create new Next.js project with App Router
3. Copy over only necessary files

### Phase 2: File Structure Changes
```
OLD (CRA):                          NEW (Next.js):
frontend/src/
  index.js ——————————————————→ app/layout.js
  index.css ———————————————→ (merge into layout or globals.css)
  App.js ———————————————————→ app/page.js
  App.css ———————————————————→ app/page.css
  components/ ——————————————→ app/components/
    FileUpload.js ———————→ app/components/FileUpload.js
    FileUpload.css ———————→ app/components/FileUpload.css
    PlayerConfig.js ———→ app/components/PlayerConfig.js
    PlayerConfig.css ———→ app/components/PlayerConfig.css
    ArrangementDisplay.js → app/components/ArrangementDisplay.js
    ArrangementDisplay.css → app/components/ArrangementDisplay.css
  public/favicon.ico ———————→ public/favicon.ico (same location)
```

### Phase 3: Code Updates
1. Remove index.js/index.css (replaced by layout.js)
2. Remove App.test.js, setupTests.js (CRA testing files)
3. Update CSS imports (no changes needed - CSS Modules work)
4. Update component imports (adjust relative paths)
5. App.js → page.js (rename, no code changes)

### Phase 4: Configuration
1. Create next.config.js (empty or with defaults)
2. Create .env.local (if needed for API URL)
3. Update package.json scripts
4. Remove CRA-specific config

### Phase 5: Testing
1. `npm run dev` - verify dev server
2. Test file upload
3. Test API calls to backend
4. Test all UI components
5. `npm run build` - verify production build

---

## Detailed Changes

### Files to Create
- `app/layout.js` - Root layout (replaces index.js root render)
- `app/page.js` - Home page (replaces App.js)
- `app/page.module.css` or `app/globals.css` - Styling
- `next.config.js` - Next.js configuration
- `.env.local` - Environment variables

### Files to Delete
- `src/index.js` (replaced by layout.js)
- `src/index.css` (merge into globals)
- `src/reportWebVitals.js` (CRA-specific)
- `src/setupTests.js` (CRA testing)
- `src/App.test.js` (test file)
- `src/logo.svg` (unused)

### Files to Keep (Move)
- `src/App.js` → `app/page.js` (no code changes)
- `src/App.css` → `app/page.module.css` (minor adjustments)
- `src/components/*` → `app/components/*` (keep as-is)

### Package.json Changes
```json
Remove:
  - react-scripts
  - @testing-library/jest-dom
  - @testing-library/react
  - @testing-library/user-event
  - @testing-library/dom
  - setupTests reference

Add:
  - next: ^15.1.0
  - react: ^19.2.4 (keep same)
  - react-dom: ^19.2.4 (keep same)

Scripts:
  "start" → "dev": "next dev"
  "build" → "build": "next build"
  "test" → (remove, or use jest separately)
```

---

## Step-by-Step Execution

1. **Create backup** - Copy current frontend
2. **Initialize Next.js** - `npx create-next-app@latest`
3. **Migrate dependencies** - Update package.json
4. **Copy components** - Move /src/components to /app/components
5. **Create layout.js** - Root layout with styling
6. **Create page.js** - Home page from App.js
7. **Update imports** - Fix relative paths
8. **Test locally** - npm run dev
9. **Build test** - npm run build
10. **Clean up** - Remove unnecessary files

---

## Expected Outcome

✅ Same functionality as CRA
✅ Modern, maintained tooling
✅ Faster builds (Turbopack)
✅ Better error messages
✅ Ready for future optimizations (SSR, image optimization, etc.)

---

## Rollback Plan

If issues arise:
1. Keep backup of original frontend directory
2. All code changes are additive/structural
3. Can restore from backup in minutes
4. No database/backend changes

---

## Testing Checklist

After migration:
- [ ] `npm install` succeeds
- [ ] `npm run dev` starts without errors
- [ ] App loads at http://localhost:3000
- [ ] File upload works
- [ ] API calls to backend work (http://localhost:5000)
- [ ] All UI components render
- [ ] Console has no errors/warnings
- [ ] `npm run build` succeeds
- [ ] `.next/static/` folder created

---

## Completion Criteria

✅ Dev server runs successfully
✅ All components display correctly
✅ File upload to backend works
✅ API calls successful
✅ No console errors
✅ Production build succeeds
✅ Ready for deployment

