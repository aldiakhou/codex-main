import React, { useState } from 'react';

const ChatInterface: React.FC = () => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim()) {
      console.log('Sending message:', message);
      setMessage('');
    }
  };

  return (
    <div className="bg-[var(--bg-primary)] border-t border-[var(--border)] p-4">
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit}>
          <div className="relative">
            <input 
              type="text" 
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Delegate a task to Nexus AI..." 
              className="w-full bg-[var(--bg-tertiary)] rounded-lg py-3 pl-4 pr-12 text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] border border-[var(--border)]" 
            />
            <button 
              type="submit"
              className="absolute inset-y-0 right-0 flex items-center pr-4 text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
              </svg>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
