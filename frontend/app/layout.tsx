import './globals.css'

export const metadata = {
  title: 'Video Processing Dashboard',
  description: 'Distributed FFmpeg Platform',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="text-gray-900 antialiased font-sans">
        {children}
      </body>
    </html>
  )
}
