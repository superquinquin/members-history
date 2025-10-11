import { useState } from 'react'

function App() {
  const [searchName, setSearchName] = useState('')
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedMember, setSelectedMember] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001'

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchName.trim()) return

    setLoading(true)
    setError(null)
    setMembers([])
    setSelectedMember(null)

    try {
      const response = await fetch(`${apiUrl}/api/members/search?name=${encodeURIComponent(searchName)}`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to search members')
      }

      setMembers(data.members || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const selectMember = (member) => {
    setSelectedMember(member)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 shadow-lg">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold text-white drop-shadow-md">
            🛒 Superquinquin
          </h1>
          <p className="text-purple-100 mt-2 text-lg">Member History Portal</p>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8">
            <form onSubmit={handleSearch} className="mb-8">
              <label htmlFor="search-name" className="block text-lg font-semibold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
                🔍 Search Members
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="search-name"
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  className="flex-1 px-5 py-3 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-400 transition-all duration-200 text-gray-800 placeholder-gray-400"
                  placeholder="Enter member name..."
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none"
                >
                  {loading ? '🔄 Searching...' : '🔍 Search'}
                </button>
              </div>
            </form>

            {error && (
              <div className="mb-6 p-5 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl text-red-700 shadow-md">
                <span className="font-semibold">⚠️ Error:</span> {error}
              </div>
            )}

            {members.length > 0 && (
              <div className="border-t-2 border-purple-200 pt-8">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-6">
                  📋 Search Results ({members.length})
                </h2>
                <div className="grid gap-4 md:grid-cols-2">
                  {members.map((member) => (
                    <div
                      key={member.id}
                      onClick={() => selectMember(member)}
                      className={`p-5 rounded-xl cursor-pointer transition-all duration-200 transform hover:scale-105 shadow-md hover:shadow-xl ${
                        selectedMember?.id === member.id
                          ? 'bg-gradient-to-r from-purple-100 to-pink-100 border-2 border-purple-400'
                          : 'bg-white border-2 border-purple-200 hover:border-purple-300'
                      }`}
                    >
                      <div className="font-bold text-gray-900 text-lg mb-2 flex items-center gap-2">
                        👤 {member.name}
                      </div>
                      {member.address && (
                        <div className="text-sm text-gray-600 mb-1 flex items-center gap-2">
                          📍 {member.address}
                        </div>
                      )}
                      {member.phone && (
                        <div className="text-sm text-gray-600 flex items-center gap-2">
                          📞 {member.phone}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedMember && (
              <div className="border-t-2 border-purple-200 pt-8 mt-8">
                <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-xl p-6 mb-4">
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                    📊 History for {selectedMember.name}
                  </h2>
                  <p className="text-purple-700">Member ID: {selectedMember.id}</p>
                </div>
                <div className="text-center py-12 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl border-2 border-dashed border-purple-300">
                  <div className="text-6xl mb-4">🚧</div>
                  <p className="text-gray-600 text-lg font-medium">History feature coming soon</p>
                  <p className="text-gray-500 mt-2">We're working on bringing you detailed member history</p>
                </div>
              </div>
            )}

            {!loading && !error && members.length === 0 && searchName && (
              <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-purple-50 rounded-xl border-2 border-dashed border-gray-300">
                <div className="text-6xl mb-4">🔍</div>
                <p className="text-gray-600 text-lg font-medium">No members found</p>
                <p className="text-gray-500 mt-2">Try searching with a different name</p>
              </div>
            )}

            {!loading && !error && members.length === 0 && !searchName && (
              <div className="text-center py-16 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border-2 border-dashed border-purple-300">
                <div className="text-6xl mb-4">👆</div>
                <p className="text-gray-600 text-lg font-medium">Start by searching for a member</p>
                <p className="text-gray-500 mt-2">Enter a name in the search box above</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
