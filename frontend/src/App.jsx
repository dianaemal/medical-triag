import { useState } from 'react'
import axios from 'axios'
import ChatMessage from './components/ChatMessage'
import TriageResult from './components/TriageResult'
import InputForm from './components/InputForm'

const API_BASE_URL = 'http://localhost:8000'

function App() {
  const [sessionId, setSessionId] = useState(null)
  const [messages, setMessages] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState(null)
  const [triageResult, setTriageResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const startTriage = async (symptoms) => {
    setLoading(true)
    setError(null)
    setMessages([])
    setTriageResult(null)
    setCurrentQuestion(null)

    try {
      const response = await axios.post(`${API_BASE_URL}/api/triage/start`, {
        symptoms: symptoms,
      })

      const data = response.data
      setSessionId(data.session_id)

      // Add initial user message
      setMessages([{ type: 'user', content: symptoms }])

      if (data.type === 'triage') {
        // Immediate triage result
        setTriageResult(data.triage_result)
      } else if (data.type === 'ask') {
        // Question received
        setCurrentQuestion(data.question)
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: data.question }
        ])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
      console.error('Error starting triage:', err)
    } finally {
      setLoading(false)
    }
  }

  const submitAnswer = async (answer) => {
    if (!sessionId || !currentQuestion) return

    setLoading(true)
    setError(null)

    try {
      // Add user answer to messages
      setMessages(prev => [
        ...prev,
        { type: 'user', content: answer }
      ])

      const response = await axios.post(`${API_BASE_URL}/api/triage/answer`, {
        session_id: sessionId,
        answer: answer,
      })

      const data = response.data
      setCurrentQuestion(null)

      if (data.type === 'triage') {
        // Final triage result
        setTriageResult(data.triage_result)
      } else if (data.type === 'ask') {
        // Another question
        setCurrentQuestion(data.question)
        setMessages(prev => [
          ...prev,
          { type: 'assistant', content: data.question }
        ])
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred. Please try again.')
      console.error('Error submitting answer:', err)
    } finally {
      setLoading(false)
    }
  }

  const resetSession = () => {
    setSessionId(null)
    setMessages([])
    setCurrentQuestion(null)
    setTriageResult(null)
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">Medical Triage Assistant</h1>
              <p className="text-gray-600 mt-1">AI-powered symptom assessment and triage</p>
            </div>
            <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
          </div>
          {triageResult && (
            <div className="mt-4">
              <button
                onClick={resetSession}
                className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg transition-colors"
              >
                Start New Session
              </button>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6 rounded">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Chat Messages */}
        {messages.length > 0 && !triageResult && (
          <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Conversation</h2>
            <div className="space-y-4">
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} type={msg.type} content={msg.content} />
              ))}
            </div>
          </div>
        )}

        {/* Triage Result */}
        {triageResult && (
          <TriageResult result={triageResult} />
        )}

        {/* Input Form */}
        {!triageResult && (
          <div className="bg-white rounded-lg shadow-lg p-6">
            {sessionId && currentQuestion ? (
              <InputForm
                onSubmit={submitAnswer}
                placeholder="Your answer..."
                label="Answer the question"
                loading={loading}
              />
            ) : (
              <InputForm
                onSubmit={startTriage}
                placeholder="Describe your symptoms..."
                label="What are your symptoms?"
                loading={loading}
              />
            )}
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-6 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
          <p className="text-sm text-yellow-800">
            <strong>Disclaimer:</strong> This is an AI-powered triage assistant and should not replace professional medical advice. 
            In case of emergency, please call 911 immediately.
          </p>
        </div>
      </div>
    </div>
  )
}

export default App

