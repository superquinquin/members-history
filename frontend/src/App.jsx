import { useState } from 'react'

function App() {
  const [memberId, setMemberId] = useState('')

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Superquinquin - Member History
          </h1>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-6">
              <label htmlFor="member-id" className="block text-sm font-medium text-gray-700 mb-2">
                Member ID
              </label>
              <input
                type="text"
                id="member-id"
                value={memberId}
                onChange={(e) => setMemberId(e.target.value)}
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md px-4 py-2 border"
                placeholder="Enter member ID"
              />
            </div>
            
            <div className="border-t border-gray-200 pt-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">History Timeline</h2>
              <div className="text-gray-500 text-center py-8">
                Enter a member ID to view their history
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
