import './globals.css';

export const metadata = {
  title: 'Vibebells - Handbell Arrangement Generator',
  description: 'Automated handbell arrangements from MIDI and MusicXML files. Generate professional arrangements with quality scoring, hand assignment optimization, and CSV export.',
  keywords: 'handbell, arrangement, MIDI, MusicXML, bell assignment, church music',
  authors: [{ name: 'Vibebells Team' }],
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#8B2942" />
      </head>
      <body>{children}</body>
    </html>
  );
}
