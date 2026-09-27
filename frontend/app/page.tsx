export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            PayWise
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI Personal Spending Agent
          </p>
          <div className="flex gap-4 justify-center">
            <a
              href="/auth/login"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Login
            </a>
            <a
              href="/auth/register"
              className="px-6 py-3 bg-white text-gray-900 rounded-lg hover:bg-gray-50 transition border border-gray-300"
            >
              Get Started
            </a>
          </div>
        </div>
      </div>
    </main>
  )
}
