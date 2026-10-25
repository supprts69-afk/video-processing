// frontend/app/layout.tsx

export const metadata = {
  title: 'Video Processing Platform',
  description: 'Distributed FFmpeg video processing dashboard',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-white text-gray-900">
        {children}
      </body>
    </html>
  )
}
