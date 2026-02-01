import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  sendChatMessage,
  getChatHistory,
  clearChatHistory,
  getChatSuggestions
} from '../../api';

/**
 * ChatInterface - Farmer-friendly chatbot component
 * 
 * Features:
 * - Message bubbles with typing indicators
 * - Government source citations
 * - Voice input using Web Speech API
 * - Quick action suggestions
 * - Context-aware responses
 */
export default function ChatInterface({ sessionId = 'default', onClose }) {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [error, setError] = useState(null);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history and suggestions on mount
  useEffect(() => {
    loadChatHistory();
    loadSuggestions();
    initializeSpeechRecognition();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async () => {
    try {
      const data = await getChatHistory(sessionId);
      if (data.history && data.history.length > 0) {
        const formattedMessages = data.history.map(msg => ({
          role: msg.role,
          content: msg.content,
          sources: msg.sources || [],
          timestamp: msg.timestamp
        }));
        setMessages(formattedMessages);
      }
    } catch (err) {
      console.error('Failed to load chat history:', err);
    }
  };

  const loadSuggestions = async () => {
    try {
      const data = await getChatSuggestions(sessionId);
      setSuggestions(data.suggestions || []);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
    }
  };

  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-IN'; // Indian English

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        setError('Voice input failed. Please try again.');
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  };

  const handleSendMessage = async (messageText = null) => {
    const message = messageText || inputMessage.trim();
    if (!message) return;

    // Add user message to UI
    const userMessage = { role: 'user', content: message, sources: [] };
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(message, sessionId);

      // Add assistant message with sources
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        sources: response.sources || [],
        tools_used: response.tools_used || []
      };

      setMessages(prev => [...prev, assistantMessage]);

      // Update suggestions
      if (response.suggestions && response.suggestions.length > 0) {
        setSuggestions(response.suggestions);
      }

    } catch (err) {
      console.error('Chat error:', err);
      setError('Failed to get response. Please try again.');

      // Add error message
      const errorMessage = {
        role: 'assistant',
        content: 'I\'m sorry, I encountered an error. Please try asking your question again.',
        sources: [],
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      setError('Voice input not supported in your browser');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setIsListening(true);
      recognitionRef.current.start();
    }
  };

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to clear the chat history?')) {
      try {
        await clearChatHistory(sessionId);
        setMessages([]);
        loadSuggestions();
      } catch (err) {
        console.error('Failed to clear history:', err);
        setError('Failed to clear history');
      }
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
    handleSendMessage(suggestion);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-green-600 text-white rounded-t-lg">
        <div className="flex items-center gap-2">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <h3 className="text-lg font-semibold">🌾 Farming Assistant</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleClearHistory}
            className="p-2 hover:bg-green-700 rounded-full transition"
            title="Clear chat history"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-green-700 rounded-full transition"
              title="Close chat"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      </div>

      {/* Quick Suggestions */}
      {suggestions.length > 0 && messages.length === 0 && (
        <div className="p-4 border-b bg-green-50">
          <p className="text-sm text-gray-600 mb-2">Quick questions:</p>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, idx) => (
              <button
                key={idx}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1 text-sm bg-white border border-green-300 text-green-700 rounded-full hover:bg-green-100 transition"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-3 m-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center justify-between">
          <span className="text-sm">{error}</span>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isLoading && (
          <div className="text-center text-gray-500 mt-8">
            <svg className="w-16 h-16 mx-auto mb-4 text-green-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <p className="text-lg font-medium mb-2">Welcome to your Farming Assistant!</p>
            <p className="text-sm">Ask me anything about your crops, weather, market prices, or pest management.</p>
          </div>
        )}

        {messages.map((message, idx) => (
          <MessageBubble key={idx} message={message} />
        ))}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white text-sm flex-shrink-0">
              🤖
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t bg-gray-50">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about your crops, weather, prices..."
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-2xl focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
              rows="1"
              style={{ maxHeight: '120px' }}
              disabled={isLoading}
            />
            {recognitionRef.current && (
              <button
                onClick={toggleVoiceInput}
                className={`absolute right-3 bottom-3 p-2 rounded-full transition ${isListening
                    ? 'bg-red-500 text-white animate-pulse'
                    : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                  }`}
                title={isListening ? 'Stop listening' : 'Voice input'}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              </button>
            )}
          </div>
          <button
            onClick={() => handleSendMessage()}
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-3 bg-green-600 text-white rounded-2xl hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition flex items-center gap-2"
          >
            <span>Send</span>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * MessageBubble - Individual message component with source citations
 */
function MessageBubble({ message }) {
  const [showSources, setShowSources] = useState(false);

  const isUser = message.role === 'user';
  const hasError = message.isError;

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm flex-shrink-0 ${isUser ? 'bg-blue-600' : hasError ? 'bg-red-500' : 'bg-green-600'
        }`}>
        {isUser ? '👤' : hasError ? '⚠️' : '🤖'}
      </div>

      {/* Message Content */}
      <div className={`max-w-[70%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-2xl px-4 py-3 ${isUser
            ? 'bg-blue-600 text-white rounded-tr-none'
            : hasError
              ? 'bg-red-50 text-red-900 border border-red-200 rounded-tl-none'
              : 'bg-gray-100 text-gray-900 rounded-tl-none'
          }`}>
          <div className={`text-sm prose prose-sm max-w-none ${isUser
              ? 'prose-invert prose-p:my-1.5 prose-li:my-0.5'
              : hasError
                ? 'prose-p:my-1.5 prose-li:my-0.5'
                : 'prose-p:my-1.5 prose-li:my-0.5 prose-strong:font-semibold prose-strong:text-gray-900 prose-ol:list-decimal prose-ul:list-disc prose-headings:font-semibold prose-headings:text-gray-900 prose-a:text-green-700 prose-a:no-underline hover:prose-a:underline prose-code:bg-gray-200 prose-code:px-1 prose-code:rounded prose-code:text-sm'
            }`}>
            <ReactMarkdown
              components={{
                p: ({ node, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
                strong: ({ node, ...props }) => <strong className="font-semibold" {...props} />,
                ul: ({ node, ...props }) => <ul className="list-disc list-inside my-2 space-y-0.5 pl-2" {...props} />,
                ol: ({ node, ...props }) => <ol className="list-decimal list-inside my-2 space-y-0.5 pl-2" {...props} />,
                li: ({ node, ...props }) => <li className="ml-1" {...props} />,
                h1: ({ node, ...props }) => <h1 className="text-base font-bold mt-2 mb-1 first:mt-0" {...props} />,
                h2: ({ node, ...props }) => <h2 className="text-sm font-bold mt-2 mb-1 first:mt-0" {...props} />,
                h3: ({ node, ...props }) => <h3 className="text-sm font-semibold mt-2 mb-1 first:mt-0" {...props} />,
                a: ({ node, ...props }) => <a className="text-green-700 underline hover:no-underline" target="_blank" rel="noopener noreferrer" {...props} />,
                code: ({ node, ...props }) => (
                  <code className="bg-gray-200/80 px-1 rounded text-xs font-mono" {...props} />
                ),
                pre: ({ node, ...props }) => (
                  <pre className="bg-gray-200/80 p-2 rounded text-xs overflow-x-auto my-2" {...props} />
                ),
              }}
            >
              {message.content || ''}
            </ReactMarkdown>
          </div>
        </div>

        {/* Source Citations */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 ml-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="text-xs text-green-600 hover:text-green-700 flex items-center gap-1"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{showSources ? 'Hide' : 'Show'} Sources ({message.sources.length})</span>
            </button>

            {showSources && (
              <div className="mt-2 space-y-1">
                {message.sources.map((source, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-xs text-gray-600 bg-white px-3 py-2 rounded-lg border border-gray-200">
                    <svg className="w-3 h-3 mt-0.5 text-green-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span>{source}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
