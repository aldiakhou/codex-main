import React, { useState, useEffect } from 'react';

const ErrorBanner: React.FC<{ message: string | null | undefined }> = ({ message }) => {
  const [visible, setVisible] = useState(false);
  const [text, setText] = useState<string>('');
  useEffect(() => {
    if (message) {
      setText(message);
      setVisible(true);
    }
  }, [message]);
  if (!visible || !text) return null;
  return (
    <div className="max-w-4xl mx-auto px-4 mb-2">
      <div className="flex items-center justify-between bg-red-500/20 border border-red-500/40 text-red-200 px-3 py-2 rounded">
        <div className="text-sm truncate">{text}</div>
        <button className="text-xs px-2 py-1 rounded bg-red-500/20 border border-red-500/40" onClick={() => setVisible(false)}>Dismiss</button>
      </div>
    </div>
  );
};

export default ErrorBanner;

