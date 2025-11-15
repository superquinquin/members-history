/**
 * Unit tests for getEventTitle() function.
 * 
 * Tests the logic that determines the correct translation key for shift events
 * based on shift type (FTOP vs Standard) and state (done/absent/excused).
 */
import { describe, it, expect } from 'vitest'

/**
 * Extract getEventTitle function from App.jsx for testing.
 * In a real implementation, this should be moved to a separate utility file.
 */
const getEventTitle = (event, t) => {
  if (event.type === 'purchase') return t('timeline.purchase')
  if (event.type === 'leave_start') return t('timeline.leaveStart')
  if (event.type === 'leave_end') return t('timeline.leaveEnd')
  if (event.type === 'counter') return t('counter.manual')
  
  if (event.type === 'shift') {
    // FTOP shift titles
    if (event.shift_type === 'ftop') {
      if (event.state === 'done') return t('timeline.ftopShiftAttended')
      if (event.state === 'absent') return t('timeline.ftopShiftMissed')
      if (event.state === 'excused') return t('timeline.ftopShiftExcused')
    }
    
    // Standard shift titles (default)
    if (event.state === 'done') return t('timeline.shiftAttended')
    if (event.state === 'absent') return t('timeline.shiftMissed')
    if (event.state === 'excused') return t('timeline.shiftExcused')
  }
  
  return event.type
}

// Mock translation function
const mockT = (key) => {
  const translations = {
    'timeline.ftopShiftAttended': 'FTOP Shift Attended',
    'timeline.ftopShiftMissed': 'FTOP Shift Missed',
    'timeline.ftopShiftExcused': 'FTOP Shift Excused',
    'timeline.shiftAttended': 'Shift Attended',
    'timeline.shiftMissed': 'Shift Missed',
    'timeline.shiftExcused': 'Shift Excused',
    'timeline.purchase': 'Purchase in Store',
    'counter.manual': 'Manual Point Adjustment',
  }
  return translations[key] || key
}

describe('getEventTitle', () => {
  describe('FTOP shifts', () => {
    it('returns ftopShiftAttended for attended FTOP shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('FTOP Shift Attended')
    })
    
    it('returns ftopShiftMissed for missed FTOP shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'absent'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('FTOP Shift Missed')
    })
    
    it('returns ftopShiftExcused for excused FTOP shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'excused'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('FTOP Shift Excused')
    })
  })
  
  describe('Standard shifts', () => {
    it('returns shiftAttended for attended standard shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'done'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('Shift Attended')
    })
    
    it('returns shiftMissed for missed standard shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'absent'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('Shift Missed')
    })
    
    it('returns shiftExcused for excused standard shift', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'excused'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('Shift Excused')
    })
  })
  
  describe('Unknown shift type', () => {
    it('returns default shift title when shift_type is unknown', () => {
      const event = {
        type: 'shift',
        shift_type: 'unknown',
        state: 'done'
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('Shift Attended')
    })
    
    it('returns default shift title when shift_type is missing', () => {
      const event = {
        type: 'shift',
        state: 'done'
        // No shift_type field
      }
      
      const result = getEventTitle(event, mockT)
      
      expect(result).toBe('Shift Attended')
    })
  })
  
  describe('Other event types', () => {
    it('returns purchase title for purchase events', () => {
      const event = { type: 'purchase' }
      const result = getEventTitle(event, mockT)
      expect(result).toBe('Purchase in Store')
    })
    
    it('returns manual counter title for counter events', () => {
      const event = { type: 'counter' }
      const result = getEventTitle(event, mockT)
      expect(result).toBe('Manual Point Adjustment')
    })
  })
})
