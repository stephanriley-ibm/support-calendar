/**
 * Timezone utility functions for handling global team timezones
 */

/**
 * Get the user's browser timezone
 * @returns {string} IANA timezone string (e.g., 'America/Denver')
 */
export const getBrowserTimezone = () => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch (error) {
    console.error('Failed to detect browser timezone:', error);
    return 'UTC';
  }
};

/**
 * Common timezone list for selection dropdown
 */
export const COMMON_TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'America/Anchorage', label: 'Alaska' },
  { value: 'Pacific/Honolulu', label: 'Hawaii' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris, Berlin, Rome' },
  { value: 'Europe/Athens', label: 'Athens, Istanbul' },
  { value: 'Asia/Dubai', label: 'Dubai' },
  { value: 'Asia/Kolkata', label: 'India' },
  { value: 'Asia/Shanghai', label: 'Beijing, Shanghai' },
  { value: 'Asia/Tokyo', label: 'Tokyo' },
  { value: 'Australia/Sydney', label: 'Sydney' },
  { value: 'Pacific/Auckland', label: 'Auckland' },
];

/**
 * Format a date string in the user's timezone
 * @param {string} dateString - ISO date string (YYYY-MM-DD)
 * @param {string} timezone - IANA timezone string
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted date string
 */
export const formatDateInTimezone = (dateString, timezone = 'UTC', options = {}) => {
  if (!dateString) return '';
  
  try {
    // For date-only strings, append time to avoid timezone conversion issues
    const date = new Date(dateString + 'T12:00:00Z');
    
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      timeZone: timezone,
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(date);
  } catch (error) {
    console.error('Failed to format date:', error);
    return dateString;
  }
};

/**
 * Format a datetime string in the user's timezone
 * @param {string} datetimeString - ISO datetime string
 * @param {string} timezone - IANA timezone string
 * @param {object} options - Intl.DateTimeFormat options
 * @returns {string} Formatted datetime string
 */
export const formatDateTimeInTimezone = (datetimeString, timezone = 'UTC', options = {}) => {
  if (!datetimeString) return '';
  
  try {
    const date = new Date(datetimeString);
    
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: timezone,
      timeZoneName: 'short',
    };
    
    return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(date);
  } catch (error) {
    console.error('Failed to format datetime:', error);
    return datetimeString;
  }
};

/**
 * Format time in the user's timezone
 * @param {string} timeString - Time string (HH:MM:SS or HH:MM)
 * @param {string} dateString - Date string for context (YYYY-MM-DD)
 * @param {string} timezone - IANA timezone string
 * @returns {string} Formatted time string
 */
export const formatTimeInTimezone = (timeString, dateString, timezone = 'UTC') => {
  if (!timeString) return '';
  
  try {
    // Combine date and time to create a full datetime
    const datetime = new Date(`${dateString}T${timeString}Z`);
    
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      timeZone: timezone,
      timeZoneName: 'short',
    }).format(datetime);
  } catch (error) {
    console.error('Failed to format time:', error);
    return timeString;
  }
};

/**
 * Get timezone offset string (e.g., "UTC-7" or "UTC+5:30")
 * @param {string} timezone - IANA timezone string
 * @returns {string} Offset string
 */
export const getTimezoneOffset = (timezone = 'UTC') => {
  try {
    const now = new Date();
    const formatter = new Intl.DateTimeFormat('en-US', {
      timeZone: timezone,
      timeZoneName: 'short',
    });
    
    const parts = formatter.formatToParts(now);
    const timeZoneName = parts.find(part => part.type === 'timeZoneName')?.value || '';
    
    return timeZoneName;
  } catch (error) {
    console.error('Failed to get timezone offset:', error);
    return 'UTC';
  }
};

/**
 * Convert a date to ISO format for API submission (always in UTC)
 * @param {Date|string} date - Date object or string
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
export const toISODate = (date) => {
  if (!date) return '';
  
  try {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toISOString().split('T')[0];
  } catch (error) {
    console.error('Failed to convert to ISO date:', error);
    return '';
  }
};

/**
 * Check if a timezone string is valid
 * @param {string} timezone - IANA timezone string
 * @returns {boolean} True if valid
 */
export const isValidTimezone = (timezone) => {
  try {
    Intl.DateTimeFormat(undefined, { timeZone: timezone });
    return true;
  } catch (error) {
    return false;
  }
};

// Made with Bob
