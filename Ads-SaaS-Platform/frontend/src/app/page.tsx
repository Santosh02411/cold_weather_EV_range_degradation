import { redirect } from 'next/navigation'

export default function Home() {
  // Redirect to dashboard for authenticated users or login for unauthenticated
  redirect('/login')
}
