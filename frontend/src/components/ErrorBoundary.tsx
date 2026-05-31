import { Component } from "react";
import type { ErrorInfo, ReactNode } from "react";
import { AlertTriangle, RefreshCw, Home } from "lucide-react";
import { logger } from "../utils/logger";
import { API_BASE_URL } from "../config/api";
import { getCookie } from "../utils/cookies";
import * as Sentry from "@sentry/react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    Sentry.captureException(error, { extra: errorInfo });
    // Log to production error tracking service
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
    };

    const csrfToken = getCookie("csrf_token");

    fetch(`${API_BASE_URL}/errors/client`, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
      },
      body: JSON.stringify(errorData),
    }).catch((err) => {
      logger.error("Failed to log error to backend", err);
      logger.error("Original error", { error, errorInfo });
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
    window.location.href = "/";
  };

  handleRefresh = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-linear-to-br from-gray-50 via-red-50/30 to-orange-50/30 flex items-center justify-center p-6">
          <div className="max-w-2xl text-center animate-fadeIn">
            <div className="mb-8 flex justify-center">
              <div className="p-6 bg-red-100 rounded-full animate-shake">
                <AlertTriangle size={80} className="text-red-600" />
              </div>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Oops! Something Broke
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Don't worry, we've caught this error and our team has been
              notified.
            </p>
            {this.state.error && import.meta.env.DEV && (
              <div className="mb-8 p-6 bg-red-50 border border-red-200 rounded-xl text-left overflow-auto">
                <h3 className="font-bold text-red-900 mb-2">Error Details:</h3>
                <pre className="text-xs text-red-800 whitespace-pre-wrap">
                  {this.state.error.toString()}
                </pre>
              </div>
            )}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={this.handleRefresh}
                className="flex items-center justify-center gap-2 px-8 py-4 bg-linear-to-r from-red-500 to-orange-500 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition"
              >
                <RefreshCw size={20} />
                Refresh
              </button>
              <button
                onClick={this.handleReset}
                className="flex items-center justify-center gap-2 px-8 py-4 bg-white border border-gray-200 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 hover:shadow-lg transition"
              >
                <Home size={20} />
                Go Home
              </button>
            </div>{" "}
            <div className="mt-12 pt-8 border-t border-gray-200">
              <p className="text-sm text-gray-600">
                If this keeps happening, please{" "}
                <a
                  href="/contact"
                  className="text-blue-600 font-semibold hover:underline"
                >
                  contact support
                </a>
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
