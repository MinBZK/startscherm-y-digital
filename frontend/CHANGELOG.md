## Changelog

### 12-02-2025

Project setup

- Added Next.js 15
- Added React 19\*
- Added D3
- Added zustand for managing global client state
- Bun for package manager / build tool / runtime\*\*
- Added tailwind for styling
- Added eslint for linting

\* React 19 is stable for a couple of months now.

\*\* I chose bun as the package manager / build tool / runtime because it's faster than npm and yarn and I expect less dependency issues with React 19. If we need to switch to npm or yarn, we can do it later.

### 19-02-2025

- Set up Docker environment
- Node visualization (force-directed graph?)
- componenten skeletons (tanstack table)
- create a util function to merge tailwind classes
- Get an idea on why to choose JSONLD over regular JSON
- Build in the overheid branding (font, colors, etc.)
- Set up the beginning of the custimizable design system
- environment variables and upgrade to tailwind v4
- Add a basic chat interface
- Added logos to the project
- Added a validation text component
- Added a textarea component that resizes based on the content

### 26-02-2025

- Implement chat ui
- Added sidebar
- Implement Source UI
- Scroll logic in chat for multiple messages
- Filter logic
- Search query
- Client state
- Data access layer
- Added basic animation
- Hover states

### 26-03-2025

- Refactor to new JSON (data)
- Implemented badges for the sources
- Created markdown displayer
- Styled the markdown displayer
- More refactoring to match the new design
- Marked text for the taxonomy

Up next

- Sidebar content aanpassen naar design
- Selectielijsten integreren in de sidebar
- Source detail scherm maken in de sidebar
- Corresponderende hover styling

### COMMANDS

### Bun

| Bun Command | npm Command |

| Bun Command | npm Command     |
| ----------- | --------------- |
| `bun add`   | `npm install`   |
| `bun build` | `npm run build` |
| `bun dev`   | `npm run dev`   |
| `bunx`      | `npx`           |

### Docker

```bash
docker build -t bsw-frontend .
docker run -p 31033:3000 bsw-frontend
```
