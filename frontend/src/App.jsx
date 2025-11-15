import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import cyclesData from '../../data/cycles_2025.json'

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
    setLeaves([])
    setHistoryError(null)
    setHistoryLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/member/${member.id}/history`)
      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error || 'Failed to fetch history')
      }

      setHistoryEvents(data.events || [])
      setLeaves(data.leaves || [])
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

  const formatDateShort = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return new Intl.DateTimeFormat(i18n.language, {
      month: 'short',
      day: 'numeric'
    }).format(date)
  }

  const getCycleAndWeekForDate = (dateString) => {
    if (!dateString) return null
    
    const eventDate = new Date(dateString)
    const dateStr = eventDate.toISOString().split('T')[0]
    
    for (const cycle of cyclesData.cycles) {
      for (const week of cycle.weeks) {
        if (dateStr >= week.start_date && dateStr <= week.end_date) {
          return {
            cycleNumber: cycle.cycle_number,
            cycleStartDate: cycle.start_date,
            cycleEndDate: cycle.end_date,
            weekLetter: week.week_letter,
            weekStartDate: week.start_date,
            weekEndDate: week.end_date
          }
        }
      }
    }
    
    return null
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
    
    if (leaves) {
      leaves.forEach(leave => {
        const leaveStart = new Date(leave.start_date)
        const leaveEnd = new Date(leave.stop_date)
        
        const startCycleInfo = getCycleAndWeekForDate(leave.start_date)
        if (startCycleInfo) {
          const cycleKey = `cycle-${startCycleInfo.cycleNumber}`
          if (cycles[cycleKey]) {
            const weekKey = startCycleInfo.weekLetter
            if (!cycles[cycleKey].weeks[weekKey]) {
              cycles[cycleKey].weeks[weekKey] = {
                weekLetter: weekKey,
                startDate: startCycleInfo.weekStartDate,
                endDate: startCycleInfo.weekEndDate,
                events: []
              }
            }
            cycles[cycleKey].weeks[weekKey].events.push({
              type: 'leave_start',
              date: leave.start_date,
              leave_type: leave.leave_type,
              leave_end: leave.stop_date,
              leave_id: leave.id,
              weekLetter: startCycleInfo.weekLetter,
              duringLeave: false
            })
          }
        }
        
        const endCycleInfo = getCycleAndWeekForDate(leave.stop_date)
        if (endCycleInfo) {
          const cycleKey = `cycle-${endCycleInfo.cycleNumber}`
          if (cycles[cycleKey]) {
            const weekKey = endCycleInfo.weekLetter
            if (!cycles[cycleKey].weeks[weekKey]) {
              cycles[cycleKey].weeks[weekKey] = {
                weekLetter: weekKey,
                startDate: endCycleInfo.weekStartDate,
                endDate: endCycleInfo.weekEndDate,
                events: []
              }
            }
            cycles[cycleKey].weeks[weekKey].events.push({
              type: 'leave_end',
              date: leave.stop_date,
              leave_type: leave.leave_type,
              leave_start: leave.start_date,
              leave_id: leave.id,
              weekLetter: endCycleInfo.weekLetter,
              duringLeave: false
            })
          }
        }
      })
    }
    
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
                                  if (event.type === 'shift' && event.state === 'done') return '🎯'
                                  if (event.type === 'shift' && event.state === 'absent') return '❌'
                                  if (event.type === 'shift' && event.state === 'excused') return '✓'
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
                                  if (event.type === 'shift' && event.state === 'done') return 'from-green-500 to-emerald-500'
                                  if (event.type === 'shift' && event.state === 'absent') {
                                    return event.duringLeave ? 'from-gray-400 to-gray-500' : 'from-red-500 to-rose-500'
                                  }
                                  if (event.type === 'shift' && event.state === 'excused') {
                                    return event.duringLeave ? 'from-gray-400 to-gray-500' : 'from-blue-500 to-cyan-500'
                                  }
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
                  }
                                  
                                  return event.type
                                }
                                
                                return (
                                  <div key={`${event.type}-${event.id || event.leave_id}-${event.date}`} className="relative">
                                    <div className={`absolute -left-12 top-1 w-8 h-8 rounded-full bg-gradient-to-br ${getEventBgColor()} flex items-center justify-center text-white shadow-lg text-lg z-10`}>
                                      {getEventIcon()}
                                    </div>
                                    
                                    <div className={`bg-white rounded-xl p-4 shadow-md border-2 hover:shadow-lg transition-all ${(event.type === 'leave_start' || event.type === 'leave_end') ? 'border-yellow-400 bg-yellow-50' : event.type === 'counter' ? (event.point_qty > 0 ? 'border-green-400' : event.point_qty < 0 ? 'border-red-400' : 'border-gray-400') : event.duringLeave ? 'border-yellow-300 bg-yellow-50' : 'border-purple-200'}`}>
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
                                          <div className="flex items-center gap-2">
                                            <span className="font-medium">{t('timeline.leaveType')}:</span>
                                            <span>{event.leave_type || 'N/A'}</span>
                                          </div>
                                          {event.type === 'leave_start' && event.leave_end && (
                                            <div className="mt-1 text-xs text-gray-600">
                                              {t('timeline.until')}: {formatDate(event.leave_end)}
                                            </div>
                                          )}
                                          {event.type === 'leave_end' && event.leave_start && (
                                            <div className="mt-1 text-xs text-gray-600">
                                              {t('timeline.since')}: {formatDate(event.leave_start)}
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
