import { useState, useEffect } from 'react'
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
  const [leaves, setLeaves] = useState([])
  const [memberStatus, setMemberStatus] = useState(null)
  const [holidays, setHolidays] = useState([])
  const [cycleConfig, setCycleConfig] = useState(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001'

  // Fetch cycle configuration on component mount
  useEffect(() => {
    const fetchCycleConfig = async () => {
      try {
        const response = await fetch(`${apiUrl}/api/config/cycles`)
        if (response.ok) {
          const config = await response.json()
          setCycleConfig(config)
        } else {
          // Use default config if fetch fails
          console.warn('Failed to fetch cycle config, using defaults')
          setCycleConfig({
            weeks_per_cycle: 4,
            week_a_date: '2025-01-13'
          })
        }
      } catch (err) {
        console.warn('Error fetching cycle config:', err)
        // Use default config
        setCycleConfig({
          weeks_per_cycle: 4,
          week_a_date: '2025-01-13'
        })
      }
    }

    fetchCycleConfig()
  }, [apiUrl])

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
    setLeaves([])
    setMemberStatus(null)
    setHolidays([])
    setHistoryError(null)
    setHistoryLoading(true)

    try {
      // Fetch member history (required)
      const historyResponse = await fetch(`${apiUrl}/api/member/${member.id}/history`)

      if (!historyResponse.ok) {
        const historyData = await historyResponse.json()
        throw new Error(historyData.error || 'Failed to fetch history')
      }

      const historyData = await historyResponse.json()
      setHistoryEvents(historyData.events || [])
      setLeaves(historyData.leaves || [])
      setHolidays(historyData.holidays || [])

      // Fetch member status (optional - don't fail if this errors)
      try {
        const statusResponse = await fetch(`${apiUrl}/api/member/${member.id}/status`)
        if (statusResponse.ok) {
          const statusData = await statusResponse.json()
          setMemberStatus(statusData)
        } else {
          console.warn('Failed to fetch member status, continuing without it')
        }
      } catch (statusErr) {
        console.warn('Error fetching member status:', statusErr)
        // Continue without status - it's not critical
      }
    } catch (err) {
      setHistoryError(err.message || 'An error occurred')
      console.error('Error fetching member data:', err)
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

  const formatDateShort = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return new Intl.DateTimeFormat(i18n.language, {
      month: 'short',
      day: 'numeric'
    }).format(date)
  }

  const getCycleAndWeekForDate = (dateString) => {
    if (!dateString || !cycleConfig) return null

    const eventDate = new Date(dateString)
    const weekAStart = new Date(cycleConfig.week_a_date)
    const weeksPerCycle = cycleConfig.weeks_per_cycle

    // Calculate days since Week A start
    const daysDiff = Math.floor((eventDate - weekAStart) / (1000 * 60 * 60 * 24))

    if (daysDiff < 0) {
      // Date is before Week A start
      return null
    }

    // Calculate total weeks since Week A
    const totalWeeks = Math.floor(daysDiff / 7)

    // Calculate cycle number (1-indexed)
    const cycleNumber = Math.floor(totalWeeks / weeksPerCycle) + 1

    // Calculate week within cycle (0-indexed)
    const weekInCycle = totalWeeks % weeksPerCycle

    // Map to week letter
    const weekLetters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    const weekLetter = weekLetters[weekInCycle]

    // Calculate week boundaries
    const weekOffsetDays = totalWeeks * 7
    const weekStart = new Date(weekAStart)
    weekStart.setDate(weekStart.getDate() + weekOffsetDays)
    const weekEnd = new Date(weekStart)
    weekEnd.setDate(weekEnd.getDate() + 6)

    // Calculate cycle boundaries
    const cycleWeekOffset = (cycleNumber - 1) * weeksPerCycle * 7
    const cycleStart = new Date(weekAStart)
    cycleStart.setDate(cycleStart.getDate() + cycleWeekOffset)
    const cycleEnd = new Date(cycleStart)
    cycleEnd.setDate(cycleEnd.getDate() + (weeksPerCycle * 7) - 1)

    return {
      cycleNumber,
      cycleStartDate: cycleStart.toISOString().split('T')[0],
      cycleEndDate: cycleEnd.toISOString().split('T')[0],
      weekLetter,
      weekStartDate: weekStart.toISOString().split('T')[0],
      weekEndDate: weekEnd.toISOString().split('T')[0]
    }
  }

  const isEventDuringLeave = (eventDate, leaves) => {
    if (!eventDate || !leaves || leaves.length === 0) return null

    const eventDateStr = new Date(eventDate).toISOString().split('T')[0]

    for (const leave of leaves) {
      if (eventDateStr >= leave.start_date && eventDateStr <= leave.stop_date) {
        return leave
      }
    }

    return null
  }

  const isEventDuringHoliday = (eventDate, holidays) => {
    if (!eventDate || !holidays || holidays.length === 0) return null

    const eventDateStr = new Date(eventDate).toISOString().split('T')[0]

    for (const holiday of holidays) {
      if (eventDateStr >= holiday.date_begin && eventDateStr <= holiday.date_end) {
        return holiday
      }
    }

    return null
  }

  const formatDateRange = (startDate, endDate) => {
    const start = new Date(startDate)
    const end = new Date(endDate)
    const startFormatted = new Intl.DateTimeFormat(i18n.language, {
      month: 'short',
      day: 'numeric'
    }).format(start)
    const endFormatted = new Intl.DateTimeFormat(i18n.language, {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    }).format(end)
    return `${startFormatted} - ${endFormatted}`
  }

  const groupEventsByCycle = (events, leaves) => {
    const cycles = {}
    const allEvents = []
    
    events.forEach(event => {
      const cycleInfo = getCycleAndWeekForDate(event.date)
      if (!cycleInfo) return
      
      const cycleKey = `cycle-${cycleInfo.cycleNumber}`
      
      if (!cycles[cycleKey]) {
        cycles[cycleKey] = {
          cycleNumber: cycleInfo.cycleNumber,
          startDate: cycleInfo.cycleStartDate,
          endDate: cycleInfo.cycleEndDate,
          weeks: {},
          leaves: [],
          allEvents: []
        }
      }
      
      const weekKey = cycleInfo.weekLetter
      if (!cycles[cycleKey].weeks[weekKey]) {
        cycles[cycleKey].weeks[weekKey] = {
          weekLetter: weekKey,
          startDate: cycleInfo.weekStartDate,
          endDate: cycleInfo.weekEndDate,
          events: []
        }
      }
      
      const duringLeave = isEventDuringLeave(event.date, leaves)
      
      const eventWithMeta = {
        ...event,
        weekLetter: cycleInfo.weekLetter,
        duringLeave: duringLeave
      }
      
      cycles[cycleKey].weeks[weekKey].events.push(eventWithMeta)
      cycles[cycleKey].allEvents.push(eventWithMeta)
      allEvents.push({ ...eventWithMeta, cycleKey })
    })

    // Note: Leave start/end events are now created by the backend and included in the events array
    // The leaves array is still needed for the isEventDuringLeave() helper to show overlays on shifts

    return Object.values(cycles).sort((a, b) => b.cycleNumber - a.cycleNumber)
  }

  const getWeekLabelColor = (weekName) => {
    if (!weekName) return 'text-gray-500'
    const colors = {
      'A': 'text-blue-600',
      'B': 'text-green-600',
      'C': 'text-yellow-600',
      'D': 'text-purple-600'
    }
    return colors[weekName] || 'text-gray-500'
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
                  <p className="text-purple-700 mb-3">{t('history.memberId')} {selectedMember.id}</p>

                  {/* Member Status Badges */}
                  {memberStatus && (
                    <div className="flex flex-wrap gap-2 mt-4">
                      {(() => {
                        // Calculate attended standard shifts in last 13 cycles (excluding current)
                        const getAttendedStandardShiftsCount = () => {
                          if (!memberStatus || memberStatus.shift_type !== 'standard' || !cycleConfig) return null

                          const today = new Date().toISOString().split('T')[0]
                          const currentCycleInfo = getCycleAndWeekForDate(today)

                          if (!currentCycleInfo) return null

                          const currentCycleNumber = currentCycleInfo.cycleNumber
                          const startCycleNumber = currentCycleNumber - 13

                          const count = historyEvents.filter(event => {
                            // Only count shift events with standard type
                            if (event.type !== 'shift' || event.shift_type !== 'standard') return false

                            // Check if attended (done, late but attended, or excused)
                            const isAttended = event.state === 'done' || event.is_late === true || event.state === 'excused'
                            if (!isAttended) return false

                            // Get event's cycle
                            const eventCycleInfo = getCycleAndWeekForDate(event.date)
                            if (!eventCycleInfo) return false

                            // Include if in last 13 cycles but not current cycle
                            return eventCycleInfo.cycleNumber < currentCycleNumber &&
                                   eventCycleInfo.cycleNumber >= startCycleNumber
                          }).length

                          return count
                        }

                        const attendedShiftsCount = getAttendedStandardShiftsCount()

                        return (
                          <>
                      {/* Cooperative State Badge */}
                      {memberStatus.cooperative_state && (
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                          memberStatus.cooperative_state === 'up_to_date' ? 'bg-green-100 text-green-800 border border-green-300' :
                          memberStatus.cooperative_state === 'alert' ? 'bg-yellow-100 text-yellow-800 border border-yellow-300' :
                          memberStatus.cooperative_state === 'suspended' || memberStatus.cooperative_state === 'blocked' ? 'bg-red-100 text-red-800 border border-red-300' :
                          memberStatus.cooperative_state === 'delay' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                          'bg-gray-100 text-gray-800 border border-gray-300'
                        }`}>
                          {memberStatus.cooperative_state === 'up_to_date' && '✓'}
                          {memberStatus.cooperative_state === 'alert' && '⚠️'}
                          {memberStatus.cooperative_state === 'suspended' && '🚫'}
                          {memberStatus.cooperative_state === 'blocked' && '🚫'}
                          {memberStatus.cooperative_state === 'delay' && '⏱️'}
                          {' '}
                          {t(`status.${memberStatus.cooperative_state}`)}
                        </span>
                      )}

                      {/* Shift Type Badge */}
                      {memberStatus.shift_type && (
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                          memberStatus.shift_type === 'ftop' ? 'bg-purple-100 text-purple-800 border border-purple-300' :
                          'bg-blue-100 text-blue-800 border border-blue-300'
                        }`}>
                          {memberStatus.shift_type === 'ftop' ? '⏱️' : '📅'}
                          {' '}
                          {memberStatus.shift_type === 'ftop' ? t('counter.ftop') : t('counter.standard')}
                        </span>
                      )}

                      {/* Shopping Privileges */}
                      {memberStatus.customer !== undefined && (
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${
                          memberStatus.customer ? 'bg-green-100 text-green-800 border border-green-300' :
                          'bg-gray-100 text-gray-800 border border-gray-300'
                        }`}>
                          {memberStatus.customer ? '🛒' : '🚫'}
                          {' '}
                          {memberStatus.customer ? t('status.canShop') : t('status.cannotShop')}
                        </span>
                      )}

                      {/* Standard Shifts Count Badge */}
                      {attendedShiftsCount !== null && (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold bg-indigo-100 text-indigo-800 border border-indigo-300">
                          📅 {attendedShiftsCount} {t('history.shiftsInLast13Cycles')}
                        </span>
                      )}
                          </>
                        )
                      })()}
                    </div>
                  )}

                  {/* Counter Summary Widget */}
                  {historyEvents.length > 0 && (
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
                      {(() => {
                        // Find the most recent counter totals from events
                        // Search through ALL events to find both counter values
                        let latestFtopTotal = null
                        let latestStandardTotal = null

                        // Iterate through events to find the latest counter values
                        // Events are sorted most recent first, so we capture first occurrence of each counter
                        for (const event of historyEvents) {
                          if (event.type === 'shift' && event.counter) {
                            // Shift events with counter data should have both totals
                            if (event.counter.ftop_total !== undefined && latestFtopTotal === null) {
                              latestFtopTotal = event.counter.ftop_total
                            }
                            if (event.counter.standard_total !== undefined && latestStandardTotal === null) {
                              latestStandardTotal = event.counter.standard_total
                            }
                          }
                          if (event.type === 'counter') {
                            // Manual counter events have both totals regardless of type
                            if (event.ftop_total !== undefined && latestFtopTotal === null) {
                              latestFtopTotal = event.ftop_total
                            }
                            if (event.standard_total !== undefined && latestStandardTotal === null) {
                              latestStandardTotal = event.standard_total
                            }
                          }

                          // Stop searching once we have both values
                          if (latestFtopTotal !== null && latestStandardTotal !== null) {
                            break
                          }
                        }

                        // If we still don't have values, default to 0 (member with no counter events yet)
                        if (latestFtopTotal === null) latestFtopTotal = 0
                        if (latestStandardTotal === null) latestStandardTotal = 0

                        const getCounterStatusColor = (value, isFtop) => {
                          if (value === null || value === undefined) return 'text-gray-600'
                          if (isFtop) {
                            // FTOP counter can be positive (encouraged!)
                            if (value > 0) return 'text-green-600'
                            if (value === 0) return 'text-blue-600'
                            return 'text-orange-600'
                          } else {
                            // Standard counter should be 0
                            if (value === 0) return 'text-green-600'
                            return 'text-red-600'
                          }
                        }

                        const getCounterStatus = (value, isFtop) => {
                          if (value === null || value === undefined) return t('counter.noData')
                          if (isFtop) {
                            if (value > 0) return t('counter.ftopPositive')
                            if (value === 0) return t('counter.ftopZero')
                            return t('counter.ftopNegative')
                          } else {
                            if (value === 0) return t('counter.standardUpToDate')
                            return t('counter.standardNegative')
                          }
                        }

                        return (
                          <>
                            {/* FTOP Counter */}
                            {latestFtopTotal !== null && (
                              <div className="bg-white rounded-lg p-4 shadow-sm border-2 border-purple-200">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="text-2xl">⏱️</span>
                                    <div>
                                      <div className="text-xs text-gray-500 font-medium">{t('counter.ftop')}</div>
                                      <div className={`text-2xl font-bold ${getCounterStatusColor(latestFtopTotal, true)}`}>
                                        {latestFtopTotal > 0 && '+'}{latestFtopTotal}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="text-xs text-gray-500 text-right">
                                    {getCounterStatus(latestFtopTotal, true)}
                                  </div>
                                </div>
                              </div>
                            )}

                            {/* Standard Counter */}
                            {latestStandardTotal !== null && (
                              <div className="bg-white rounded-lg p-4 shadow-sm border-2 border-blue-200">
                                <div className="flex items-center justify-between">
                                  <div className="flex items-center gap-2">
                                    <span className="text-2xl">📅</span>
                                    <div>
                                      <div className="text-xs text-gray-500 font-medium">{t('counter.standard')}</div>
                                      <div className={`text-2xl font-bold ${getCounterStatusColor(latestStandardTotal, false)}`}>
                                        {latestStandardTotal > 0 && '+'}{latestStandardTotal}
                                      </div>
                                    </div>
                                  </div>
                                  <div className="text-xs text-gray-500 text-right">
                                    {getCounterStatus(latestStandardTotal, false)}
                                  </div>
                                </div>
                              </div>
                            )}
                          </>
                        )
                      })()}
                    </div>
                  )}
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
                  <div className="relative space-y-8">
                    {groupEventsByCycle(historyEvents, leaves).map((cycle) => {
                      const cycleStartDate = new Date(cycle.startDate)
                      const cycleEndDate = new Date(cycle.endDate)
                      const cycleDuration = cycleEndDate - cycleStartDate
                      
                      return (
                      <div key={`cycle-${cycle.cycleNumber}`} className="relative">
                        <div className="absolute inset-0 bg-gradient-to-l from-gray-50 to-gray-100 opacity-50 rounded-xl" />
                        
                        <div className="relative grid grid-cols-[112px_1fr] gap-4 p-4">
                          <div className="flex-shrink-0 text-right pt-2 pr-12">
                            <div className="text-sm font-bold text-gray-600">
                              {t('timeline.cycle')} {cycle.cycleNumber}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {formatDateShort(cycle.startDate)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {formatDateShort(cycle.endDate)}
                            </div>
                          </div>
                          
                          <div className="relative min-h-[200px]">
                            <div className="pl-12 space-y-8">
                              {Object.values(cycle.weeks).sort((a, b) => 
                                b.startDate.localeCompare(a.startDate)
                              ).map((week) => (
                                <div key={week.weekLetter} className="relative">
                                  <div className="absolute -left-8 top-0 bottom-0 w-0.5 bg-gradient-to-b from-purple-300 to-pink-300" />
                                  
                                  <div className={`absolute -left-24 top-1 text-2xl font-bold ${getWeekLabelColor(week.weekLetter)}`}>
                                    {week.weekLetter}
                                  </div>
                                  
                                  <div className="space-y-6">
                                    {week.events.sort((a, b) => 
                                      new Date(b.date) - new Date(a.date)
                                    ).map((event) => {
                                const getEventIcon = () => {
                                  if (event.type === 'purchase') return '🛒'
                                  if (event.type === 'leave_start') return '🏖️'
                                  if (event.type === 'leave_end') return '🔙'
                                  if (event.type === 'counter') return '⚖️'

                                  // Check for technical FTOP shift (cycle deduction)
                                  if (event.type === 'shift' && event.shift_type === 'ftop' && event.state === 'done' && event.counter && event.counter.point_qty === -1) {
                                    return '⚙️'
                                  }

                                  if (event.type === 'shift' && event.state === 'done') return '🎯'
                                  if (event.type === 'shift' && event.state === 'absent') return '❌'
                                  if (event.type === 'shift' && event.state === 'excused') return '📝'
                                  // Show exchange icon only for actual exchanges
                                  if (event.type === 'shift' && (event.state === 'waiting' || event.state === 'replaced') && event.exchange_details) return '🔄'
                                  // Waiting/replaced without exchange (during leave) - use excused icon
                                  if (event.type === 'shift' && (event.state === 'waiting' || event.state === 'replaced')) return '📝'
                                  return '📋'
                                }
                                
                                const getEventBgColor = () => {
                                  if (event.type === 'purchase') return 'from-purple-500 to-pink-500'
                                  if (event.type === 'leave_start') return 'from-yellow-500 to-amber-500'
                                  if (event.type === 'leave_end') return 'from-yellow-500 to-amber-500'
                                  if (event.type === 'counter') {
                                    if (event.point_qty > 0) return 'from-green-500 to-emerald-500'
                                    if (event.point_qty < 0) return 'from-red-500 to-rose-500'
                                    return 'from-gray-500 to-slate-500'
                                  }

                                  // Check for technical FTOP shift (cycle deduction) - use neutral color
                                  if (event.type === 'shift' && event.shift_type === 'ftop' && event.state === 'done' && event.counter && event.counter.point_qty === -1) {
                                    return 'from-gray-500 to-slate-500'
                                  }

                                  if (event.type === 'shift' && event.state === 'done') return 'from-green-500 to-emerald-500'
                                  if (event.type === 'shift' && event.state === 'absent') {
                                    return event.duringLeave ? 'from-gray-400 to-gray-500' : 'from-red-500 to-rose-500'
                                  }
                                  if (event.type === 'shift' && event.state === 'excused') {
                                    return event.duringLeave ? 'from-gray-400 to-gray-500' : 'from-blue-500 to-cyan-500'
                                  }
                                  if (event.type === 'shift' && event.state === 'waiting') return 'from-orange-500 to-amber-500'
                                  if (event.type === 'shift' && event.state === 'replaced') return 'from-orange-500 to-amber-500'
                                  return 'from-gray-500 to-slate-500'
                                }
                                
                                const getEventTitle = () => {
                                  if (event.type === 'purchase') return t('timeline.purchase')
                                  if (event.type === 'leave_start') return t('timeline.leaveStart')
                                  if (event.type === 'leave_end') return t('timeline.leaveEnd')
                                  if (event.type === 'counter') return t('counter.manual')

                                  // Shift events - check shift type
                                  if (event.type === 'shift') {
                                    const isFtop = event.shift_type === 'ftop'

                                    // Check for technical FTOP shift (cycle deduction)
                                    if (isFtop && event.state === 'done' && event.counter && event.counter.point_qty === -1) {
                                      return t('shift.ftopCycleDeduction')
                                    }

                                    // FTOP shifts: always show "FTOP shift closed" regardless of state
                                    if (isFtop) {
                                      return t('timeline.ftopShiftAttended')
                                    }

                                    // Standard shifts: show state-specific labels
                                    if (event.state === 'done') {
                                      return t('timeline.shiftAttended')
                                    }
                                    if (event.state === 'absent') {
                                      return t('timeline.shiftMissed')
                                    }
                                    if (event.state === 'excused') {
                                      return t('timeline.shiftExcused')
                                    }
                                    // Show "Shift Exchanged" ONLY if there's actual exchange data
                                    if ((event.state === 'waiting' || event.state === 'replaced') && event.exchange_details) {
                                      return t('timeline.shiftExchanged')
                                    }
                                    // Waiting/replaced without exchange data (e.g., during leave) - treat as excused
                                    if (event.state === 'waiting' || event.state === 'replaced') {
                                      return t('timeline.shiftExcused')
                                    }
                                  }

                                  return event.type
                                }
                                
                                return (
                                  <div key={`${event.type}-${event.id || event.leave_id}-${event.date}`} className="relative">
                                    <div className={`absolute -left-12 top-1 w-8 h-8 rounded-full bg-gradient-to-br ${getEventBgColor()} flex items-center justify-center text-white shadow-lg text-lg z-10`}>
                                      {getEventIcon()}
                                    </div>
                                    
                                    <div className={`bg-white rounded-xl p-4 shadow-md border-2 hover:shadow-lg transition-all ${
                                      (event.type === 'leave_start' || event.type === 'leave_end') ? 'border-yellow-400 bg-yellow-50' :
                                      event.type === 'counter' ? (event.point_qty > 0 ? 'border-green-400' : event.point_qty < 0 ? 'border-red-400' : 'border-gray-400') :
                                      event.type === 'shift' && (event.is_exchanged || event.is_exchange) && event.exchange_details ? 'border-orange-300 bg-orange-50' :
                                      event.duringLeave ? 'border-yellow-300 bg-yellow-50' :
                                      'border-purple-200'
                                    }`}>
                                      <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center gap-2">
                                          <span className="font-semibold text-gray-900">{getEventTitle()}</span>
                                          {event.shift_type === 'unknown' && (
                                            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
                                              ⚠️ {t('timeline.shiftTypeWarning')}
                                            </span>
                                          )}
                                          {event.duringLeave && (
                                            <span className="text-xs bg-yellow-200 text-yellow-800 px-2 py-0.5 rounded-full">
                                              {t('timeline.duringLeave')}
                                            </span>
                                          )}
                                          {event.type === 'shift' && event.is_exchanged && event.exchange_details && (
                                            <span className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full">
                                              🔄 {t('shift.exchanged')}
                                            </span>
                                          )}
                                          {event.type === 'shift' && event.is_exchange && event.exchange_details && (
                                            <span className="text-xs bg-blue-200 text-blue-800 px-2 py-0.5 rounded-full">
                                              ↔️ {t('shift.exchange')}
                                            </span>
                                          )}
                                        </div>
                                        <span className="text-sm text-purple-600 font-medium">{formatDate(event.date)}</span>
                                      </div>
                                      {event.type === 'purchase' && event.reference && (
                                        <div className="text-xs text-gray-500">
                                          {t('timeline.reference')}: {event.reference}
                                        </div>
                                      )}
                                      {(event.type === 'leave_start' || event.type === 'leave_end') && (
                                        <div className="text-sm text-gray-700 mt-2">
                                          <div className="flex items-center justify-between gap-2 mb-2">
                                            <div className="flex items-center gap-2">
                                              <span className="font-medium">{t('timeline.leaveType')}:</span>
                                              <span className="font-semibold text-yellow-800">{event.leave_type || 'N/A'}</span>
                                            </div>
                                            {event.type === 'leave_start' && event.leave_end && (() => {
                                              const start = new Date(event.date)
                                              const end = new Date(event.leave_end)
                                              const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24))
                                              return (
                                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full font-medium">
                                                  📅 {days} {days === 1 ? t('leave.day') : t('leave.days')}
                                                </span>
                                              )
                                            })()}
                                          </div>
                                          {event.type === 'leave_start' && event.leave_end && (
                                            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs">
                                              <div className="flex items-start gap-2">
                                                <span>📅</span>
                                                <div>
                                                  <div className="font-medium text-yellow-900 mb-1">{t('leave.period')}</div>
                                                  <div className="text-gray-700">
                                                    {formatDate(event.date)} → {formatDate(event.leave_end)}
                                                  </div>
                                                  <div className="mt-1 text-yellow-700 italic">
                                                    💡 {t('leave.noPenalty')}
                                                  </div>
                                                  {event.leave_type && event.leave_type.toLowerCase().includes('vacation') && (
                                                    <div className="mt-1 text-purple-700 text-xs">
                                                      ⏱️ {t('leave.ftopPointUsed')}
                                                    </div>
                                                  )}
                                                </div>
                                              </div>
                                            </div>
                                          )}
                                          {event.type === 'leave_end' && event.leave_start && (
                                            <div className="mt-1 text-xs text-gray-600 flex items-center gap-1">
                                              <span>🔙</span>
                                              <span>{t('timeline.since')}: {formatDate(event.leave_start)}</span>
                                            </div>
                                          )}
                                        </div>
                                      )}
                                      {event.type === 'shift' && (
                                        <div className="text-sm text-gray-700 mt-2">
                                          <div className="flex items-center justify-between gap-2">
                                            <div className="flex items-center gap-2">
                                              <span className="font-medium">{t('timeline.shiftName')}:</span>
                                              <span>{event.shift_name || 'N/A'}</span>
                                            </div>
                                            {event.counter && (
                                              <div className={`text-sm font-semibold ${event.counter.point_qty > 0 ? 'text-green-600' : event.counter.point_qty < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                                                <span className="mr-1">{event.counter.type === 'ftop' ? '⏱️' : '📅'}</span>
                                                <span className="text-xs font-medium mr-1">
                                                  {event.counter.type === 'ftop' ? t('counter.ftop_short') : t('counter.standard_short')}
                                                </span>
                                                {event.counter.point_qty > 0 ? '+' : ''}{event.counter.point_qty}
                                                <span className="text-gray-600 ml-1">
                                                  → {event.counter.type === 'ftop' ? event.counter.ftop_total : event.counter.standard_total}
                                                </span>
                                              </div>
                                            )}
                                          </div>

                                          {/* Holiday Relief Explanation */}
                                          {event.state === 'absent' && event.counter && (() => {
                                            const holiday = isEventDuringHoliday(event.date, holidays)
                                            if (holiday) {
                                              // Calculate penalty breakdown
                                              // Base penalty is -2, holiday relief adds back 1 or 2
                                              const netPenalty = event.counter.point_qty
                                              const basePenalty = -2
                                              const relief = netPenalty - basePenalty // This will be +1 or +2

                                              return (
                                                <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                                                  <div className="text-xs font-semibold text-yellow-800 mb-1">
                                                    🎉 {t('holiday.duringHoliday')}: {holiday.name}
                                                  </div>
                                                  <div className="text-xs text-gray-700">
                                                    <div className="flex justify-between items-center">
                                                      <span>{t('holiday.basePenalty')}:</span>
                                                      <span className="font-mono text-red-600">{basePenalty}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center">
                                                      <span>{t('holiday.relief')}:</span>
                                                      <span className="font-mono text-green-600">+{relief}</span>
                                                    </div>
                                                    <div className="flex justify-between items-center font-semibold border-t border-yellow-300 mt-1 pt-1">
                                                      <span>{t('holiday.netPenalty')}:</span>
                                                      <span className="font-mono text-orange-700">{netPenalty}</span>
                                                    </div>
                                                  </div>
                                                  <div className="text-xs text-yellow-700 mt-1 italic">
                                                    {formatDate(holiday.date_begin)} - {formatDate(holiday.date_end)}
                                                  </div>
                                                </div>
                                              )
                                            }
                                            return null
                                          })()}

                                          {/* FTOP Cycle Deduction Explanation */}
                                          {event.shift_type === 'ftop' && event.state === 'done' && event.counter && event.counter.point_qty === -1 && (
                                            <div className="mt-2 p-2 bg-gray-50 border border-gray-300 rounded">
                                              <div className="text-xs text-gray-700">
                                                <div className="flex items-start gap-2">
                                                  <span className="text-base">ℹ️</span>
                                                  <div>
                                                    <div className="font-medium text-gray-800 mb-1">
                                                      {t('shift.ftopCycleExplanation')}
                                                    </div>
                                                    <div className="text-xs text-gray-600 italic">
                                                      {t('shift.ftopCycleDetail')}
                                                    </div>
                                                  </div>
                                                </div>
                                              </div>
                                            </div>
                                          )}

                                          {/* Exchange Details */}
                                          {event.exchange_details &&
                                           event.exchange_details.exchange_state &&
                                           event.exchange_details.exchange_state !== 'draft' && (
                                            <div className="mt-2 p-3 bg-orange-50 border border-orange-200 rounded">
                                              <div className="text-xs text-gray-700">
                                                <div className="flex items-start gap-2">
                                                  <span className="text-base">🔄</span>
                                                  <div className="flex-1">
                                                    <div className="font-semibold text-orange-900 mb-2">
                                                      {t('exchange.details')}
                                                    </div>

                                                    {/* Original shift that was exchanged away */}
                                                    {event.exchange_details.replacement_shift && event.exchange_details.replacement_shift.date && (
                                                      <div className="mb-2 p-2 bg-white rounded border border-orange-100">
                                                        <div className="font-medium text-orange-800 mb-1">
                                                          {t('exchange.replacedWith')}
                                                        </div>
                                                        <div className="text-gray-700">
                                                          <div>{event.exchange_details.replacement_shift.shift_name || t('exchange.shift')}</div>
                                                          <div className="text-xs text-gray-600 mt-1">
                                                            📅 {formatDate(event.exchange_details.replacement_shift.date)}
                                                            {event.exchange_details.replacement_shift.week_name && (
                                                              <span className="ml-2">• Week {event.exchange_details.replacement_shift.week_name}</span>
                                                            )}
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}

                                                    {/* Replacement shift that replaced an original */}
                                                    {event.exchange_details.original_shift && event.exchange_details.original_shift.date && (
                                                      <div className="mb-2 p-2 bg-white rounded border border-blue-100">
                                                        <div className="font-medium text-blue-800 mb-1">
                                                          {t('exchange.replaces')}
                                                        </div>
                                                        <div className="text-gray-700">
                                                          <div>{event.exchange_details.original_shift.shift_name || t('exchange.shift')}</div>
                                                          <div className="text-xs text-gray-600 mt-1">
                                                            📅 {formatDate(event.exchange_details.original_shift.date)}
                                                            {event.exchange_details.original_shift.week_name && (
                                                              <span className="ml-2">• Week {event.exchange_details.original_shift.week_name}</span>
                                                            )}
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}

                                                    {/* Counter impact explanation */}
                                                    {event.exchange_details.counter_impact && (
                                                      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded">
                                                        <div className="flex items-start gap-2">
                                                          <span className="text-sm">✓</span>
                                                          <div className="text-xs text-green-800">
                                                            {event.exchange_details.counter_impact === 'no_penalty_attended_replacement' && (
                                                              <span>{t('exchange.noPenaltyAttended')}</span>
                                                            )}
                                                            {event.exchange_details.counter_impact === 'exchanged_for_replacement' && (
                                                              <span>{t('exchange.exchangedForReplacement')}</span>
                                                            )}
                                                          </div>
                                                        </div>
                                                      </div>
                                                    )}

                                                    {/* Show exchange state if no other details available */}
                                                    {!event.exchange_details.replacement_shift?.date &&
                                                     !event.exchange_details.original_shift?.date &&
                                                     !event.exchange_details.counter_impact &&
                                                     event.exchange_details.exchange_state && (
                                                      <div className="text-xs text-gray-600">
                                                        {t('exchange.state')}: <span className="capitalize">{event.exchange_details.exchange_state}</span>
                                                      </div>
                                                    )}
                                                  </div>
                                                </div>
                                              </div>
                                            </div>
                                          )}

                                          {event.is_late && (
                                            <div className="mt-1 text-xs text-orange-600 font-medium">
                                              ⏰ {t('timeline.shiftLate')}
                                            </div>
                                          )}
                                          {event.duringLeave && (event.state === 'absent' || event.state === 'excused') && (
                                            <div className="mt-1 text-xs text-yellow-700 font-medium">
                                              🏖️ {t('timeline.coveredByLeave')}
                                            </div>
                                          )}
                                        </div>
                                        )}
                                      {event.type === 'counter' && (
                                        <div className="text-sm text-gray-700 mt-2">
                                          <div className="flex items-center gap-2 mb-1">
                                            <span className="text-lg">{event.counter_type === 'ftop' ? '⏱️' : '📅'}</span>
                                            <span className="text-sm font-semibold mr-2">
                                              {event.counter_type === 'ftop' ? t('counter.ftop_short') : t('counter.standard_short')}
                                            </span>
                                            <span className={`text-2xl font-bold ${event.point_qty > 0 ? 'text-green-600' : event.point_qty < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                                              {event.point_qty > 0 ? '+' : ''}{event.point_qty}
                                            </span>
                                            <span className="text-gray-500">
                                              → {event.counter_type === 'ftop' ? event.ftop_total : event.standard_total}
                                            </span>
                                          </div>
                                          {event.name && (
                                            <div className="text-xs text-gray-600 mt-1">
                                              {event.name}
                                            </div>
                                          )}
                                        </div>
                                        )}
                                      </div>
                                    </div>
                                  )
                                    })}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    )}
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
