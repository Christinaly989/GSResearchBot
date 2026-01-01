import { useState, useEffect } from 'react'

function App() {
  const [status, setStatus] = useState('idle')
  const [logs, setLogs] = useState<string[]>([])
  const [companies, setCompanies] = useState('')
  const [loading, setLoading] = useState(false)

  // Poll status and logs
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('/api/status')
        const data = await res.json()
        setStatus(data.status)
        setLogs(data.logs || [])
      } catch (err) {
        // console.error(err)
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  const handleInit = async () => {
    setLoading(true)
    try {
      await fetch('/api/init', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ download_dir: 'downloads' })
      })
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  const handleConfirmLogin = async () => {
    setLoading(true)
    try {
      await fetch('/api/confirm-login', { method: 'POST' })
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  const handleProcess = async () => {
    if (!companies.trim()) return
    setLoading(true)
    try {
      const companyList = companies.split(',').map(c => c.trim()).filter(c => c)
      await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ companies: companyList })
      })
    } catch (err) {
      console.error(err)
    }
    setLoading(false)
  }

  const handleStop = async () => {
    try {
      await fetch('/api/stop', { method: 'POST' })
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto bg-white rounded-xl shadow-md overflow-hidden p-6">
        <h1 className="text-3xl font-bold mb-6 text-gray-800">GS Research Automation</h1>
        
        <div className="mb-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Controls */}
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold mb-2">1. Initialization</h2>
              <button 
                onClick={handleInit}
                disabled={status !== 'idle' && status !== 'error'}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Launch Browser
              </button>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold mb-2">2. Authentication</h2>
              <p className="text-sm text-gray-600 mb-2">
                Log in manually in the opened Chrome window, then click confirm.
              </p>
              <button 
                onClick={handleConfirmLogin}
                disabled={status !== 'login_pending'}
                className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                I Have Logged In
              </button>
            </div>

            <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h2 className="text-lg font-semibold mb-2">3. Research</h2>
              <textarea
                value={companies}
                onChange={(e) => setCompanies(e.target.value)}
                placeholder="Enter companies (e.g. Apple, Tesla, Google)"
                className="w-full p-2 border rounded mb-2 h-24 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button 
                onClick={handleProcess}
                disabled={status !== 'ready' && status !== 'processing'} // Allow adding more? maybe not for now
                className="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Research
              </button>
            </div>
            
            <div className="p-4 bg-red-50 rounded-lg border border-red-200">
               <button 
                onClick={handleStop}
                className="w-full bg-red-600 text-white py-2 px-4 rounded hover:bg-red-700"
              >
                Stop / Close Browser
              </button>
            </div>
          </div>

          {/* Status & Logs */}
          <div className="flex flex-col h-full">
            <div className="mb-4">
              <span className="font-semibold text-gray-700">Current Status: </span>
              <span className={`font-bold uppercase ${
                status === 'idle' ? 'text-gray-500' :
                status === 'processing' ? 'text-blue-600' :
                status === 'error' ? 'text-red-600' :
                'text-green-600'
              }`}>
                {status.replace('_', ' ')}
              </span>
            </div>
            
            <div className="flex-1 bg-black text-green-400 p-4 rounded-lg font-mono text-sm overflow-y-auto max-h-[500px] flex flex-col-reverse">
              {logs.length === 0 ? (
                <div className="text-gray-500 italic">No logs yet...</div>
              ) : (
                logs.slice().reverse().map((log, i) => (
                  <div key={i} className="mb-1 border-b border-gray-800 pb-1">{log}</div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
