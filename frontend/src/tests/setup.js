import '@testing-library/jest-dom'
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock i18next for tests
import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

i18n
  .use(initReactI18next)
  .init({
    lng: 'en',
    fallbackLng: 'en',
    resources: {
      en: {
        translation: {
          'timeline.ftopShiftAttended': 'FTOP Shift Attended',
          'timeline.ftopShiftMissed': 'FTOP Shift Missed',
          'timeline.ftopShiftExcused': 'FTOP Shift Excused',
          'timeline.shiftAttended': 'Shift Attended',
          'timeline.shiftMissed': 'Shift Missed',
          'timeline.shiftExcused': 'Shift Excused',
          'timeline.unknownShiftType': 'Unknown Shift Type',
          'timeline.purchase': 'Purchase in Store',
          'counter.ftop_short': 'FTOP',
          'counter.standard_short': 'ABCD',
        }
      }
    }
  })
