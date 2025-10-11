import { useState } from 'react'
import { useTranslation } from 'react-i18next'

function App() {
  const { t, i18n } = useTranslation()
  const [searchName, setSearchName] = useState('')
  const [members, setMembers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedMember, setSelectedMember] = useState(null)
  const [historyEvents, setHistoryEvents] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001'

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'fr' : 'en'
    i18n.changeLanguage(newLang)
  }

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

  const selectMember = async (member) => {
    setSelectedMember(member)
    setHistoryEvents([])
    setHistoryError(null)
    setHistoryLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/member/${member.id}/history`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch history')
      }

      setHistoryEvents(data.events || [])
    } catch (err) {
      setHistoryError(err.message)
    } finally {
      setHistoryLoading(false)
    }
  }

  const getImageSrc = (imageData) => {
    if (imageData && imageData !== false) {
      return `data:image/png;base64,${imageData}`
    }
    return null
  }

  const getInitials = (name) => {
    if (!name) return '?'
    const parts = name.split(',').map(p => p.trim())
    if (parts.length >= 2) {
      return parts[0][0] + parts[1][0]
    }
    const words = name.split(' ')
    if (words.length >= 2) {
      return words[0][0] + words[1][0]
    }
    return name[0]
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return new Intl.DateTimeFormat(i18n.language, {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-blue-50">
      <header className="bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 shadow-lg">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-4xl font-bold text-white drop-shadow-md">
                🛒 {t('app.title')}
              </h1>
              <p className="text-purple-100 mt-2 text-lg">{t('app.subtitle')}</p>
            </div>
            <button
              onClick={toggleLanguage}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-all duration-200 backdrop-blur-sm border border-white/30 font-medium"
              title={t('language.switch')}
            >
              {i18n.language === 'en' ? '🇫🇷 FR' : '🇬🇧 EN'}
            </button>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto py-8 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/20 p-8">
            <form onSubmit={handleSearch} className="mb-8">
              <label htmlFor="search-name" className="block text-lg font-semibold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-3">
                🔍 {t('search.label')}
              </label>
              <div className="flex gap-3">
                <input
                  type="text"
                  id="search-name"
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                  className="flex-1 px-5 py-3 border-2 border-purple-200 rounded-xl focus:ring-4 focus:ring-purple-300 focus:border-purple-400 transition-all duration-200 text-gray-800 placeholder-gray-400"
                  placeholder={t('search.placeholder')}
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="px-8 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105 disabled:transform-none"
                >
                  {loading ? `🔄 ${t('search.searching')}` : `🔍 ${t('search.button')}`}
                </button>
              </div>
            </form>

            {error && (
              <div className="mb-6 p-5 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl text-red-700 shadow-md">
                <span className="font-semibold">⚠️ {t('error.label')}</span> {error}
              </div>
            )}

            {members.length > 0 && (
              <div className="border-t-2 border-purple-200 pt-8">
                <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-6">
                  📋 {t('results.title')} ({members.length})
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
                      <div className="flex items-start gap-4">
                        <div className="flex-shrink-0">
                          {getImageSrc(member.image) ? (
                            <img
                              src={getImageSrc(member.image)}
                              alt={member.name}
                              className="w-16 h-16 rounded-full object-cover border-2 border-purple-300 shadow-md"
                            />
                          ) : (
                            <div className="w-16 h-16 rounded-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center text-white font-bold text-xl border-2 border-purple-300 shadow-md">
                              {getInitials(member.name)}
                            </div>
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-bold text-gray-900 text-lg mb-2">
                            {member.name}
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
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedMember && (
              <div className="border-t-2 border-purple-200 pt-8 mt-8">
                <div className="bg-gradient-to-r from-purple-100 to-pink-100 rounded-xl p-6 mb-6">
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                    📊 {t('history.title', { name: selectedMember.name })}
                  </h2>
                  <p className="text-purple-700">{t('history.memberId')} {selectedMember.id}</p>
                </div>

                {historyLoading ? (
                  <div className="text-center py-12 bg-white rounded-xl border-2 border-purple-200">
                    <div className="text-4xl mb-4">⏳</div>
                    <p className="text-gray-600 font-medium">{t('timeline.loading')}</p>
                  </div>
                ) : historyError ? (
                  <div className="p-5 bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-xl text-red-700 shadow-md">
                    <span className="font-semibold">⚠️ {t('error.label')}</span> {historyError}
                  </div>
                ) : historyEvents.length > 0 ? (
                  <div className="relative">
                    <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-300 to-pink-300" />
                    
                    {historyEvents.map((event) => {
                      const getEventIcon = () => {
                        if (event.type === 'purchase') return '🛒'
                        if (event.type === 'shift' && event.state === 'done') return '🎯'
                        if (event.type === 'shift' && event.state === 'absent') return '❌'
                        if (event.type === 'shift' && event.state === 'excused') return '✓'
                        return '📋'
                      }
                      
                      const getEventBgColor = () => {
                        if (event.type === 'purchase') return 'from-purple-500 to-pink-500'
                        if (event.type === 'shift' && event.state === 'done') return 'from-green-500 to-emerald-500'
                        if (event.type === 'shift' && event.state === 'absent') return 'from-red-500 to-rose-500'
                        if (event.type === 'shift' && event.state === 'excused') return 'from-blue-500 to-cyan-500'
                        return 'from-gray-500 to-slate-500'
                      }
                      
                      const getEventTitle = () => {
                        if (event.type === 'purchase') return t('timeline.purchase')
                        if (event.type === 'shift' && event.state === 'done') return t('timeline.shiftAttended')
                        if (event.type === 'shift' && event.state === 'absent') return t('timeline.shiftMissed')
                        if (event.type === 'shift' && event.state === 'excused') return t('timeline.shiftExcused')
                        return event.type
                      }
                      
                      return (
                        <div key={`${event.type}-${event.id}`} className="relative pl-20 pb-8 last:pb-0">
                          <div className={`absolute left-4 top-0 w-8 h-8 rounded-full bg-gradient-to-br ${getEventBgColor()} flex items-center justify-center text-white shadow-lg text-lg`}>
                            {getEventIcon()}
                          </div>
                          
                          <div className="bg-white rounded-xl p-4 shadow-md border-2 border-purple-200 hover:shadow-lg transition-all">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-semibold text-gray-900">{getEventTitle()}</span>
                              <span className="text-sm text-purple-600 font-medium">{formatDate(event.date)}</span>
                            </div>
                            {event.type === 'purchase' && event.reference && (
                              <div className="text-xs text-gray-500">
                                {t('timeline.reference')}: {event.reference}
                              </div>
                            )}
                            {event.type === 'shift' && (
                              <div className="text-sm text-gray-700 mt-2">
                                <div className="flex items-center gap-2">
                                  <span className="font-medium">{t('timeline.shiftName')}:</span>
                                  <span>{event.shift_name || 'N/A'}</span>
                                </div>
                                {event.is_late && (
                                  <div className="mt-1 text-xs text-orange-600 font-medium">
                                    ⏰ {t('timeline.shiftLate')}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-purple-50 rounded-xl border-2 border-dashed border-gray-300">
                    <div className="text-6xl mb-4">📭</div>
                    <p className="text-gray-600 text-lg font-medium">{t('timeline.noHistory')}</p>
                    <p className="text-gray-500 mt-2">{t('timeline.noHistoryHint')}</p>
                  </div>
                )}
              </div>
            )}

            {!loading && !error && members.length === 0 && searchName && (
              <div className="text-center py-16 bg-gradient-to-br from-gray-50 to-purple-50 rounded-xl border-2 border-dashed border-gray-300">
                <div className="text-6xl mb-4">🔍</div>
                <p className="text-gray-600 text-lg font-medium">{t('results.noResults')}</p>
                <p className="text-gray-500 mt-2">{t('results.noResultsHint')}</p>
              </div>
            )}

            {!loading && !error && members.length === 0 && !searchName && (
              <div className="text-center py-16 bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border-2 border-dashed border-purple-300">
                <div className="text-6xl mb-4">👆</div>
                <p className="text-gray-600 text-lg font-medium">{t('results.startSearching')}</p>
                <p className="text-gray-500 mt-2">{t('results.startSearchingHint')}</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
