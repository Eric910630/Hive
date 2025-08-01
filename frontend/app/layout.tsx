import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Hive AI 助手',
  description: '您的个人AI工作流操作系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  )
} 