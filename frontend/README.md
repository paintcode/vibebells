# Vibebells Frontend

Next.js web application for the Vibebells handbell arrangement generator.

## Tech Stack

- **Next.js**: App Router architecture
- **React**: UI components
- **CSS**: Custom styling with CSS Grid/Flexbox

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The frontend expects the backend API to be running on `http://localhost:5000`.

## Project Structure

```
app/
├── components/
│   ├── FileUpload.js          # Music file upload
│   ├── PlayerConfig.js        # Player configuration
│   └── ArrangementDisplay.js  # Results display with CSV export
├── layout.js                  # Root layout with metadata
├── page.js                    # Main application page
└── globals.css                # Global styles
```

## API Integration

The frontend communicates with the Flask backend using the native `fetch` API:
- `POST /health` - Backend health check
- `POST /api/generate-arrangements` - Generate arrangements from music file

## Environment Detection

The app detects whether it's running in Electron or a browser and adjusts UI accordingly (e.g., file upload dialogs).
