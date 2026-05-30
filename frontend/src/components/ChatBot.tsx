import React, { useState, useRef, useEffect } from "react";
import axios from "axios";
import { Send, Bot, User, Loader } from "lucide-react";
import { chatbotAPI } from "../services/api";
import { logger } from "../utils/logger";

interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

const ChatBot = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Ask me about crop advice, pest management, soil health, or farming practices.",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions] = useState([
    "When is the best time to plant wheat?",
    "How do I treat tomato leaf blight?",
    "What fertilizer is best for rice?",
    "How to control aphids organically?",
  ]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef<boolean>(true);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || inputMessage;
    if (!textToSend.trim() || loading) return;

    const userMessage: Message = {
      role: "user",
      content: textToSend,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputMessage("");
    setLoading(true);

    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const response = await chatbotAPI.ask(
        textToSend,
        messages.map((msg) => ({ role: msg.role, content: msg.content })),
        controller.signal
      );

      if (!isMountedRef.current) return;

      const assistantMessage: Message = {
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
      };

      // Limit messages to last 50 to prevent memory issues
      setMessages((prev) => [...prev, assistantMessage].slice(-50));
    } catch (error) {
      if (axios.isCancel(error) || (error instanceof Error && error.name === "CanceledError")) {
        return;
      }
      if (!isMountedRef.current) return;
      logger.error("Chatbot error", error);
      const errorMessage: Message = {
        role: "assistant",
        content:
          "Sorry, I encountered an error. Please make sure the backend is running and try again.",
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      if (isMountedRef.current) {
        setLoading(false);
      }
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage();
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  return (
    <div className="min-h-full bg-slate-50 p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        {" "}
        <div className="mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-3xl font-semibold text-slate-900 mb-1 sm:mb-2">
            Farmer Assistant
          </h1>
          <p className="text-slate-600 text-sm sm:text-base">
            Ask me anything about farming, crops, and agriculture
          </p>
        </div>{" "}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          {" "}
          <div className="h-72 sm:h-96 overflow-y-auto p-3 sm:p-6 space-y-3 sm:space-y-4">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 ${message.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}
              >
                <div
                  className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${message.role === "user"
                    ? "bg-blue-500 text-white"
                    : "bg-green-500 text-white"
                    }`}
                >
                  {message.role === "user" ? (
                    <User size={18} />
                  ) : (
                    <Bot size={18} />
                  )}
                </div>
                <div
                  className={`flex-1 px-4 py-3 rounded-lg ${message.role === "user"
                    ? "bg-blue-500 text-white ml-12"
                    : "bg-gray-100 text-gray-800 mr-12"
                    }`}
                >
                  <p className="text-sm whitespace-pre-wrap">
                    {message.content}
                  </p>
                  <p
                    className={`text-xs mt-1 ${message.role === "user"
                      ? "text-blue-100"
                      : "text-gray-500"
                      }`}
                  >
                    {message.timestamp.toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-green-500 text-white flex items-center justify-center">
                  <Bot size={18} />
                </div>
                <div className="bg-gray-100 px-4 py-3 rounded-lg">
                  <Loader className="animate-spin text-green-600" size={20} />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>{" "}
          {messages.length <= 1 && (
            <div className="px-6 py-4 bg-gray-50 border-t">
              <p className="text-sm text-gray-600 mb-2">Quick questions:</p>
              <div className="flex flex-wrap gap-2">
                {suggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="text-sm px-3 py-1 bg-white border border-gray-300 rounded-full hover:bg-blue-50 hover:border-blue-400 transition"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}{" "}
          <form onSubmit={handleSubmit} className="p-3 sm:p-4 border-t">
            <div className="flex gap-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about crops, diseases, fertilizers..."
                disabled={loading}
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-100"
              />
              <button
                type="submit"
                disabled={loading || !inputMessage.trim()}
                className="px-3 sm:px-6 py-3 bg-emerald-900 text-white rounded-lg hover:bg-emerald-800 disabled:bg-gray-400 transition flex items-center gap-1 sm:gap-2 shrink-0"
              >
                <Send size={18} />
                <span className="hidden sm:inline">Send</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default React.memo(ChatBot);
