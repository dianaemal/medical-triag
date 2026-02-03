function TriageResult({ result }) {
  const getLevelColor = (level) => {
    switch (level) {
      case 'call_911':
        return 'bg-red-600 text-white'
      case 'urgent_gp':
        return 'bg-orange-500 text-white'
      case 'see_gp':
        return 'bg-yellow-500 text-white'
      case 'stay_home':
        return 'bg-green-500 text-white'
      default:
        return 'bg-gray-500 text-white'
    }
  }

  const getLevelLabel = (level) => {
    switch (level) {
      case 'call_911':
        return 'Call 911 - Emergency'
      case 'urgent_gp':
        return 'Urgent Care - See GP Soon'
      case 'see_gp':
        return 'See GP - Schedule Appointment'
      case 'stay_home':
        return 'Stay Home - Self Care'
      default:
        return level
    }
  }

  const getLevelIcon = (level) => {
    switch (level) {
      case 'call_911':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'urgent_gp':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'see_gp':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
      case 'stay_home':
        return (
          <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        )
      default:
        return null
    }
  }

  const confidenceColors = {
    high: 'text-green-600',
    medium: 'text-yellow-600',
    low: 'text-red-600'
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Triage Assessment</h2>
      
      {/* Level Badge */}
      <div className={`flex items-center space-x-4 ${getLevelColor(result.level)} rounded-lg p-6 mb-6`}>
        <div className="flex-shrink-0">
          {getLevelIcon(result.level)}
        </div>
        <div>
          <h3 className="text-2xl font-bold">{getLevelLabel(result.level)}</h3>
          <p className="text-sm opacity-90 mt-1">Confidence: <span className="font-semibold capitalize">{result.confidence}</span></p>
        </div>
      </div>

      {/* What to Do */}
      {result.what_to_do && result.what_to_do.length > 0 && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Recommended Actions
          </h3>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            {result.what_to_do.map((action, idx) => (
              <li key={idx} className="pl-2">{action}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Watch For */}
      {result.watch_for && result.watch_for.length > 0 && (
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
          <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center">
            <svg className="w-5 h-5 mr-2 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Watch For
          </h3>
          <ul className="list-disc list-inside space-y-1 text-gray-700">
            {result.watch_for.map((warning, idx) => (
              <li key={idx} className="pl-2">{warning}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default TriageResult

