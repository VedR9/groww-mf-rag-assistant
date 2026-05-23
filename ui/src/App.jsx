import { useState, useRef, useEffect } from 'react'
import './index.css'

function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  const handleReset = () => {
    setMessages([]);
    setInput('');
  }

  const handleSend = async (query) => {
    const text = typeof query === 'string' ? query : input
    if (!text.trim()) return

    const newMsg = { role: 'user', content: text }
    setMessages(prev => [...prev, newMsg])
    setInput('')
    setIsLoading(true)

    try {
      const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      
      const data = await response.json()
      
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        citationUrl: data.citation_url,
        footer: data.footer,
        refused: data.refused
      }])
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'I am unable to reach the server right now. Please ensure the backend is running.',
        refused: true
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSend()
    }
  }

  // Helper to format assistant messages correctly
  const renderMessageContent = (content) => {
    return content.split('\n').map((line, idx) => (
      <p key={idx} className={idx > 0 ? "mt-2" : ""}>{line}</p>
    ));
  }

  return (
    <div className="h-screen w-full flex flex-col overflow-hidden">
      {/* Top Header */}
      <header className="fixed top-0 left-0 w-full z-50 bg-surface/80 backdrop-blur-md shadow-sm h-16 flex items-center px-4 md:px-10 justify-between">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-primary text-3xl">account_balance_wallet</span>
          <h1 className="font-headline-md font-bold text-primary text-xl hidden sm:block">Groww Mutual Fund Assistant</h1>
        </div>
        <div className="hidden md:flex items-center px-4 py-1.5 bg-error-container/30 rounded-full border border-error/10">
          <span className="material-symbols-outlined text-error text-[18px] mr-2">warning</span>
          <span className="font-label-md text-sm text-on-surface-variant">⚠️ Facts-only Assistant: No investment advice.</span>
        </div>
        <div className="flex items-center gap-4">
          {messages.length > 0 && (
            <button 
              onClick={handleReset}
              className="flex items-center gap-2 px-4 py-2 border border-outline-variant rounded-lg text-sm font-medium text-primary hover:bg-surface-variant/50 transition-all active:scale-95 duration-150"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              Reset Chat
            </button>
          )}
        </div>
      </header>

      {/* Main Chat Canvas */}
      <main className="flex-1 overflow-y-auto pt-24 pb-48 chat-container">
        <div className="max-w-4xl mx-auto px-4 md:px-0 space-y-8">
          
          {messages.length === 0 ? (
            /* Welcome Screen */
            <section className="py-4 flex flex-col items-center text-center animate-fadeInUp">
              <div className="mb-4 p-3 bg-primary-container/20 rounded-full">
                <span className="material-symbols-outlined text-primary text-4xl">smart_toy</span>
              </div>
              <h2 className="text-2xl font-bold text-on-surface mb-2">How can I help you today?</h2>
              
              <div className="w-full max-w-2xl mb-6">
                <p className="text-secondary mb-3 text-sm">I can answer factual questions about these supported funds:</p>
                <div className="flex flex-wrap justify-center gap-2">
                  {["HDFC Mid Cap Fund", "HDFC Equity Fund", "HDFC Focused Fund", "HDFC ELSS Tax Saver", "HDFC Large Cap Fund"].map(fund => (
                    <span key={fund} className="px-3 py-1 bg-primary-container/10 text-primary border border-primary/10 rounded-full text-xs font-medium">
                      {fund}
                    </span>
                  ))}
                </div>
              </div>

              <div className="w-full max-w-xl text-left">
                <h3 className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider mb-2 px-2">Example Questions</h3>
                <div className="space-y-2">
                  {[
                    "What is the expense ratio of HDFC Mid Cap Fund Direct Growth?",
                    "What is the exit load on HDFC Large Cap Fund Direct Growth?",
                    "What is the minimum SIP amount for HDFC Equity Fund Direct Growth?",
                    "What is the riskometer for HDFC Focused Fund Direct Growth?",
                    "What is the benchmark index for HDFC ELSS Tax Saver Fund?"
                  ].map((q, idx) => (
                    <button 
                      key={idx} 
                      onClick={() => handleSend(q)}
                      className={`w-full text-left p-3 bg-white border border-outline-variant rounded-xl text-on-surface text-sm hover:bg-primary-container/5 hover:border-primary-container hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/5 transition-all animate-fadeInUp stagger-${idx+1}`}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            </section>
          ) : (
            /* Chat Thread */
            <div className="space-y-6">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 items-start animate-fadeInUp ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-secondary' : 'bg-primary'}`}>
                    <span className="material-symbols-outlined text-white text-[20px]">
                      {msg.role === 'user' ? 'person' : 'smart_toy'}
                    </span>
                  </div>
                  
                  <div className={`max-w-[80%] p-5 sm:p-6 shadow-sm border ${msg.role === 'user' ? 'bg-[#e6fcf5] rounded-2xl rounded-tr-none border-transparent' : 'bg-white rounded-2xl rounded-tl-none border-outline-variant/30 shadow-[0px_4px_20px_rgba(0,0,0,0.04)]'} ${msg.refused ? 'border-error/50 bg-error-container/10' : ''}`}>
                    <div className="space-y-3 text-on-surface text-sm sm:text-base">
                      {renderMessageContent(msg.content)}
                    </div>
                    
                    {msg.role === 'assistant' && (msg.citationUrl || msg.footer) && (
                      <div className="mt-4 pt-4 border-t border-outline-variant/20 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                        {msg.footer && <span className="text-xs text-secondary italic">{msg.footer}</span>}
                        
                        {msg.citationUrl && (
                          <a href={msg.citationUrl} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 px-3 py-1.5 bg-surface-container rounded hover:bg-surface-variant transition-colors text-xs font-medium text-primary">
                            <span className="material-symbols-outlined text-[16px]">open_in_new</span>
                            View Source
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex gap-3 items-start animate-fadeInUp">
                  <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                    <span className="material-symbols-outlined text-white text-[20px]">smart_toy</span>
                  </div>
                  <div className="bg-white px-5 py-4 rounded-2xl rounded-tl-none shadow-sm border border-outline-variant/30 flex gap-1">
                    <div className="w-2 h-2 bg-primary/40 rounded-full dot-pulse" style={{animationDelay: "0s"}}></div>
                    <div className="w-2 h-2 bg-primary/40 rounded-full dot-pulse" style={{animationDelay: "0.2s"}}></div>
                    <div className="w-2 h-2 bg-primary/40 rounded-full dot-pulse" style={{animationDelay: "0.4s"}}></div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* Bottom Input Area */}
      <div className="fixed bottom-0 left-0 w-full bg-gradient-to-t from-background via-background to-transparent pt-12 pb-8 px-4 md:px-10">
        <div className="max-w-4xl mx-auto relative group">
          <div className="flex items-center bg-white rounded-full p-2 pr-3 shadow-[0px_10px_32px_rgba(0,0,0,0.08)] border-2 border-transparent transition-all focus-within:border-primary-container focus-within:shadow-[0px_10px_40px_rgba(0,208,156,0.15)]">
            <input 
              className="flex-1 bg-transparent border-none outline-none focus:ring-0 px-6 py-4 text-on-surface placeholder:text-secondary/60" 
              placeholder="Ask a factual question about HDFC Mutual Funds..." 
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isLoading}
            />
            <div className="flex items-center gap-2">
              <button 
                onClick={() => handleSend()}
                disabled={!input.trim() || isLoading}
                className="w-12 h-12 bg-gradient-to-br from-primary-container to-primary text-white rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg shadow-primary-container/30 disabled:opacity-50 disabled:hover:scale-100"
              >
                <span className="material-symbols-outlined">arrow_upward</span>
              </button>
            </div>
          </div>
          <p className="text-center mt-3 text-xs text-secondary/60">
            © 2026 Groww Mutual Fund Assistant. Secure & Encrypted.
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
