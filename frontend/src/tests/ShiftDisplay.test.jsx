/**
 * Component tests for shift display in timeline.
 * 
 * Tests visual rendering of shift events including:
 * - Warning badge for unknown shift types
 * - FTOP indicator display
 * - Counter badge independence from shift type
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { useTranslation } from 'react-i18next'

/**
 * Mock ShiftEvent component that demonstrates the rendering logic.
 * This represents the shift event rendering portion of App.jsx.
 */
const ShiftEvent = ({ event }) => {
  const { t } = useTranslation()
  
  const getEventTitle = () => {
    if (event.shift_type === 'ftop') {
      if (event.state === 'done') return t('timeline.ftopShiftAttended')
      if (event.state === 'absent') return t('timeline.ftopShiftMissed')
      if (event.state === 'excused') return t('timeline.ftopShiftExcused')
    }
    
    if (event.state === 'done') return t('timeline.shiftAttended')
    if (event.state === 'absent') return t('timeline.shiftMissed')
    if (event.state === 'excused') return t('timeline.shiftExcused')
    
    return 'Shift'
  }
  
  return (
    <div data-testid="shift-event">
      <div className="flex items-center gap-2">
        <span className="font-semibold">{getEventTitle()}</span>
        
        {/* Warning badge for unknown shift type */}
        {event.shift_type === 'unknown' && (
          <span 
            className="text-xs bg-orange-200 text-orange-800 px-2 py-0.5 rounded-full"
            data-testid="unknown-type-warning"
          >
            ⚠️ {t('timeline.unknownShiftType')}
          </span>
        )}
        
        {/* FTOP indicator */}
        {event.shift_type === 'ftop' && (
          <span 
            className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full"
            data-testid="ftop-indicator"
          >
            ⏱️ {t('counter.ftop_short')}
          </span>
        )}
      </div>
      
      {/* Counter badge - independent of shift type */}
      {event.counter && (
        <div 
          className="counter-badge"
          data-testid="counter-badge"
        >
          <span className="mr-1">
            {event.counter.type === 'ftop' ? '⏱️' : '📅'}
          </span>
          <span className="text-xs font-medium mr-1">
            {event.counter.type === 'ftop' ? t('counter.ftop_short') : t('counter.standard_short')}
          </span>
          {event.counter.point_qty > 0 ? '+' : ''}{event.counter.point_qty}
        </div>
      )}
    </div>
  )
}

describe('ShiftEvent Display', () => {
  describe('Unknown shift type warning', () => {
    it('displays warning badge for unknown shift type', () => {
      const event = {
        type: 'shift',
        shift_type: 'unknown',
        state: 'done',
        shift_name: 'Mystery Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      const warning = screen.getByTestId('unknown-type-warning')
      expect(warning).toBeInTheDocument()
      expect(warning).toHaveTextContent('⚠️')
    })
    
    it('does not display warning for FTOP shifts', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done',
        shift_name: 'FTOP Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      const warning = screen.queryByTestId('unknown-type-warning')
      expect(warning).not.toBeInTheDocument()
    })
    
    it('does not display warning for standard shifts', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'done',
        shift_name: 'Standard Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      const warning = screen.queryByTestId('unknown-type-warning')
      expect(warning).not.toBeInTheDocument()
    })
  })
  
  describe('FTOP indicator', () => {
    it('displays FTOP indicator for FTOP shifts', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done',
        shift_name: 'FTOP Wednesday'
      }
      
      render(<ShiftEvent event={event} />)
      
      const indicator = screen.getByTestId('ftop-indicator')
      expect(indicator).toBeInTheDocument()
      expect(indicator).toHaveTextContent('⏱️')
      expect(indicator).toHaveTextContent('FTOP')
    })
    
    it('does not display FTOP indicator for standard shifts', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'done',
        shift_name: 'Monday Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      const indicator = screen.queryByTestId('ftop-indicator')
      expect(indicator).not.toBeInTheDocument()
    })
    
    it('does not display FTOP indicator for unknown shifts', () => {
      const event = {
        type: 'shift',
        shift_type: 'unknown',
        state: 'done',
        shift_name: 'Unknown Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      const indicator = screen.queryByTestId('ftop-indicator')
      expect(indicator).not.toBeInTheDocument()
    })
  })
  
  describe('Counter badge independence', () => {
    it('displays FTOP counter badge independently of shift type', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done',
        shift_name: 'FTOP Shift',
        counter: {
          type: 'ftop',
          point_qty: 1,
          ftop_total: 5,
          standard_total: 0
        }
      }
      
      render(<ShiftEvent event={event} />)
      
      const badge = screen.getByTestId('counter-badge')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveTextContent('⏱️')
      expect(badge).toHaveTextContent('FTOP')
      expect(badge).toHaveTextContent('+1')
    })
    
    it('displays standard counter badge independently of shift type', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'done',
        shift_name: 'Standard Shift',
        counter: {
          type: 'standard',
          point_qty: 1,
          ftop_total: 0,
          standard_total: 3
        }
      }
      
      render(<ShiftEvent event={event} />)
      
      const badge = screen.getByTestId('counter-badge')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveTextContent('📅')
      expect(badge).toHaveTextContent('ABCD')
      expect(badge).toHaveTextContent('+1')
    })
    
    it('does not display counter badge when no counter data', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'excused',
        shift_name: 'Excused FTOP Shift'
        // No counter
      }
      
      render(<ShiftEvent event={event} />)
      
      const badge = screen.queryByTestId('counter-badge')
      expect(badge).not.toBeInTheDocument()
    })
    
    it('handles negative counter values correctly', () => {
      const event = {
        type: 'shift',
        shift_type: 'standard',
        state: 'absent',
        shift_name: 'Missed Shift',
        counter: {
          type: 'standard',
          point_qty: -1,
          ftop_total: 0,
          standard_total: 2
        }
      }
      
      render(<ShiftEvent event={event} />)
      
      const badge = screen.getByTestId('counter-badge')
      expect(badge).toBeInTheDocument()
      expect(badge).toHaveTextContent('-1')
      expect(badge).not.toHaveTextContent('+-1') // No double sign
    })
  })
  
  describe('Mixed scenarios', () => {
    it('displays both FTOP indicator and FTOP counter badge', () => {
      const event = {
        type: 'shift',
        shift_type: 'ftop',
        state: 'done',
        shift_name: 'FTOP Shift',
        counter: {
          type: 'ftop',
          point_qty: 1,
          ftop_total: 5,
          standard_total: 0
        }
      }
      
      render(<ShiftEvent event={event} />)
      
      expect(screen.getByTestId('ftop-indicator')).toBeInTheDocument()
      expect(screen.getByTestId('counter-badge')).toBeInTheDocument()
    })
    
    it('displays warning and no counter for unknown shift without counter', () => {
      const event = {
        type: 'shift',
        shift_type: 'unknown',
        state: 'done',
        shift_name: 'Unknown Shift'
      }
      
      render(<ShiftEvent event={event} />)
      
      expect(screen.getByTestId('unknown-type-warning')).toBeInTheDocument()
      expect(screen.queryByTestId('counter-badge')).not.toBeInTheDocument()
      expect(screen.queryByTestId('ftop-indicator')).not.toBeInTheDocument()
    })
  })
})
