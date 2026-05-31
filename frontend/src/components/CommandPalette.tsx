import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Search,
  Home,
  Sprout,
  Bell,
  Settings,
  User,
  Shield,
  FileText,
  BookOpen,
  MessageSquare,
  LogOut,
  Command,
  ArrowRight,
} from "lucide-react";

interface Command {
  id: string;
  label: string;
  icon: React.ElementType;
  action: () => void;
  keywords: string[];
  category: "navigation" | "actions" | "docs";
}

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const inputRef = useRef<HTMLInputElement>(null);

  const commands: Command[] = [
    // Navigation
    {
      id: "nav-home",
      label: "Go to Dashboard",
      icon: Home,
      action: () => navigate("/dashboard"),
      keywords: ["dashboard", "home", "main"],
      category: "navigation",
    },
    {
      id: "nav-alerts",
      label: "Go to Alerts",
      icon: Bell,
      action: () => navigate("/dashboard/alerts"),
      keywords: ["alerts", "notifications", "messages"],
      category: "navigation",
    },
    {
      id: "nav-profile",
      label: "Go to Profile",
      icon: User,
      action: () => navigate("/dashboard/profile"),
      keywords: ["profile", "account", "user"],
      category: "navigation",
    },
    {
      id: "nav-agent",
      label: "Go to AI Agronomist",
      icon: Sprout,
      action: () => navigate("/dashboard/agent"),
      keywords: ["agent", "ai", "agronomist", "analysis"],
      category: "navigation",
    },
    {
      id: "nav-weather",
      label: "Go to Weather",
      icon: Settings,
      action: () => navigate("/dashboard/weather"),
      keywords: ["weather", "forecast", "climate"],
      category: "navigation",
    },
    {
      id: "nav-prices",
      label: "Go to Market Prices",
      icon: Settings,
      action: () => navigate("/dashboard/prices"),
      keywords: ["prices", "market", "mandi"],
      category: "navigation",
    },
    {
      id: "nav-yield",
      label: "Go to Yield Prediction",
      icon: Sprout,
      action: () => navigate("/dashboard/yield"),
      keywords: ["yield", "prediction", "harvest"],
      category: "navigation",
    },
    {
      id: "nav-chatbot",
      label: "Go to Chatbot",
      icon: MessageSquare,
      action: () => navigate("/dashboard/chatbot"),
      keywords: ["chatbot", "chat", "assistant"],
      category: "navigation",
    },
    {
      id: "nav-admin",
      label: "Go to Admin Panel",
      icon: Shield,
      action: () => navigate("/dashboard/admin"),
      keywords: ["admin", "management", "control"],
      category: "navigation",
    },
    // Docs
    {
      id: "nav-docs",
      label: "View Documentation",
      icon: FileText,
      action: () => navigate("/docs"),
      keywords: ["docs", "documentation", "help", "guide"],
      category: "docs",
    },
    {
      id: "nav-blog",
      label: "Read Blog",
      icon: BookOpen,
      action: () => navigate("/blog"),
      keywords: ["blog", "articles", "news"],
      category: "docs",
    },
    {
      id: "nav-contact",
      label: "Contact Support",
      icon: MessageSquare,
      action: () => navigate("/contact"),
      keywords: ["contact", "support", "help"],
      category: "docs",
    },
    // Actions
    {
      id: "action-logout",
      label: "Logout",
      icon: LogOut,
      action: () => {
        logout();
        navigate("/login");
      },
      keywords: ["logout", "signout", "exit"],
      category: "actions",
    },
  ];

  const filteredCommands = commands.filter((cmd) => {
    // Hide admin panel from non-admin users
    if (cmd.id === "nav-admin" && !user?.is_superuser) {
      return false;
    }
    return (
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.keywords.some((keyword) =>
        keyword.toLowerCase().includes(search.toLowerCase())
      )
    );
  });

  const groupedCommands = {
    navigation: filteredCommands.filter((cmd) => cmd.category === "navigation"),
    actions: filteredCommands.filter((cmd) => cmd.category === "actions"),
    docs: filteredCommands.filter((cmd) => cmd.category === "docs"),
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + K
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen(true);
      }
      // Escape
      if (e.key === "Escape") {
        setIsOpen(false);
        setSearch("");
        setSelectedIndex(0);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev < filteredCommands.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) =>
        prev > 0 ? prev - 1 : filteredCommands.length - 1
      );
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (filteredCommands[selectedIndex]) {
        executeCommand(filteredCommands[selectedIndex]);
      }
    }
  };

  const executeCommand = (command: Command) => {
    command.action();
    setIsOpen(false);
    setSearch("");
    setSelectedIndex(0);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 animate-fadeIn">
      {" "}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={() => setIsOpen(false)}
      />{" "}
      <div className="relative w-full max-w-2xl mx-4 bg-white rounded-2xl shadow-2xl animate-slideUp">
        {" "}
        <div className="flex items-center gap-3 p-4 border-b border-gray-200">
          <Search className="text-gray-400" size={20} />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedIndex(0);
            }}
            onKeyDown={handleKeyDown}
            className="flex-1 outline-none text-lg"
          />
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <kbd className="px-2 py-1 bg-gray-100 rounded font-mono">ESC</kbd>
            <span>to close</span>
          </div>
        </div>{" "}
        <div className="max-h-96 overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="py-12 text-center text-gray-500">
              No commands found
            </div>
          ) : (
            <>
              {" "}
              {groupedCommands.navigation.length > 0 && (
                <div className="mb-4">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                    Navigation
                  </div>
                  {groupedCommands.navigation.map((cmd) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    const Icon = cmd.icon;
                    return (
                      <button
                        key={cmd.id}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                        className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition ${
                          selectedIndex === globalIndex
                            ? "bg-linear-to-r from-green-50 to-emerald-50 border-l-4 border-l-green-500"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div
                          className={`p-2 rounded-lg ${
                            selectedIndex === globalIndex
                              ? "bg-green-100 text-green-600"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          <Icon size={18} />
                        </div>
                        <span className="flex-1 text-left font-medium text-gray-900">
                          {cmd.label}
                        </span>
                        {selectedIndex === globalIndex && (
                          <ArrowRight size={16} className="text-green-600" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}{" "}
              {groupedCommands.docs.length > 0 && (
                <div className="mb-4">
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                    Documentation
                  </div>
                  {groupedCommands.docs.map((cmd) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    const Icon = cmd.icon;
                    return (
                      <button
                        key={cmd.id}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                        className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition ${
                          selectedIndex === globalIndex
                            ? "bg-linear-to-r from-blue-50 to-purple-50 border-l-4 border-l-blue-500"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div
                          className={`p-2 rounded-lg ${
                            selectedIndex === globalIndex
                              ? "bg-blue-100 text-blue-600"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          <Icon size={18} />
                        </div>
                        <span className="flex-1 text-left font-medium text-gray-900">
                          {cmd.label}
                        </span>
                        {selectedIndex === globalIndex && (
                          <ArrowRight size={16} className="text-blue-600" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}{" "}
              {groupedCommands.actions.length > 0 && (
                <div>
                  <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase">
                    Actions
                  </div>
                  {groupedCommands.actions.map((cmd) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    const Icon = cmd.icon;
                    return (
                      <button
                        key={cmd.id}
                        onClick={() => executeCommand(cmd)}
                        onMouseEnter={() => setSelectedIndex(globalIndex)}
                        className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg transition ${
                          selectedIndex === globalIndex
                            ? "bg-linear-to-r from-red-50 to-orange-50 border-l-4 border-l-red-500"
                            : "hover:bg-gray-50"
                        }`}
                      >
                        <div
                          className={`p-2 rounded-lg ${
                            selectedIndex === globalIndex
                              ? "bg-red-100 text-red-600"
                              : "bg-gray-100 text-gray-600"
                          }`}
                        >
                          <Icon size={18} />
                        </div>
                        <span className="flex-1 text-left font-medium text-gray-900">
                          {cmd.label}
                        </span>
                        {selectedIndex === globalIndex && (
                          <ArrowRight size={16} className="text-red-600" />
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          )}
        </div>{" "}
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <kbd className="px-2 py-1 bg-white border border-gray-200 rounded font-mono">
              ↑↓
            </kbd>
            <span>Navigate</span>
            <kbd className="px-2 py-1 bg-white border border-gray-200 rounded font-mono">
              ↵
            </kbd>
            <span>Select</span>
          </div>
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <span>Press</span>
            <kbd className="px-2 py-1 bg-white border border-gray-200 rounded font-mono flex items-center gap-1">
              <Command size={12} />K
            </kbd>
            <span>anytime</span>
          </div>
        </div>
      </div>
    </div>
  );
};
