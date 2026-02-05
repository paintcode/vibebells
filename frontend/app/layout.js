import './globals.css';

export const metadata = {
  title: 'Handbell Arrangement Generator',
  description: 'Generate handbell arrangements for any song',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
