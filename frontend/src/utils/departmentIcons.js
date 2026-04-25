const ICON_BY_DEPARTMENT = {
  cardiology: 'cardiology',
  neurology: 'neurology',
  orthopedics: 'orthopedics',
  pediatrics: 'pediatrics',
  dermatology: 'dermatology',
  psychiatry: 'psychiatry',
  oncology: 'oncology',
  radiology: 'radiology',
  gynecology: 'pregnant_woman',
  obstetrics: 'pregnant_woman',
  dentistry: 'dentistry',
  ophthalmology: 'visibility',
  nephrology: 'water_drop',
  urology: 'urology',
  pulmonology: 'pulmonology',
  ent: 'hearing',
  surgery: 'surgical',
  emergency: 'emergency',
  general: 'local_hospital',
  medicine: 'medication',
}

function normalizeDepartmentName(value) {
  return String(value || '')
    .trim()
    .toLowerCase()
}

export function getDepartmentIconName(departmentName) {
  const normalized = normalizeDepartmentName(departmentName)
  if (!normalized) return 'local_hospital'

  if (ICON_BY_DEPARTMENT[normalized]) {
    return ICON_BY_DEPARTMENT[normalized]
  }

  const matchedKey = Object.keys(ICON_BY_DEPARTMENT).find(
    (key) => normalized.includes(key) || key.includes(normalized)
  )
  return matchedKey ? ICON_BY_DEPARTMENT[matchedKey] : 'medical_services'
}
