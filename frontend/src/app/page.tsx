"use client";
import { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import { Send, Bot, User } from "lucide-react";

export default function ChatUI() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<
    { role: string; content: string; sources?: string[] }[]
  >([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMessage = { role: "user", content: query };
    setMessages((prev) => [...prev, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const res = await axios.post("http://localhost:8000/api/v1/chat/query", {
        tenant_id: "test-tenant-123",
        query: query,
      });

      const botMessage = {
        role: "bot",
        content: res.data.answer,
        sources: res.data.sources,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", content: "Error: Could not connect to server." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50 text-gray-800">
      {/* Header */}
      <header className="bg-white shadow p-4 text-center font-bold text-xl border-b">
        Acme AI Assistant
      </header>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 max-w-4xl mx-auto w-full">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <Bot size={48} className="mx-auto mb-4 text-blue-500" />
            <p>Hello! Ask me anything about your uploaded documents.</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] p-4 rounded-lg ${msg.role === "user" ? "bg-blue-600 text-white" : "bg-white shadow border"}`}
            >
              <div className="flex items-center gap-2 mb-1">
                {msg.role === "user" ? <User size={16} /> : <Bot size={16} />}
                <span className="font-semibold text-sm">
                  {msg.role === "user" ? "You" : "Assistant"}
                </span>
              </div>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t text-xs text-gray-500">
                  <strong>Sources:</strong> {msg.sources.join(", ")}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="text-gray-500 italic">Assistant is typing...</div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t max-w-4xl mx-auto w-full">
        <form onSubmit={sendMessage} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 text-white p-3 rounded-lg hover:bg-blue-700"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
}
