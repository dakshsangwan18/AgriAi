import { useState } from "react";
import { Link } from "react-router-dom";
import { Mail, MessageSquare, Send, CheckCircle } from "lucide-react";
import { apiClient } from "../services/api";

export const ContactPage: React.FC = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: "",
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await apiClient.post("/contact", formData);
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setFormData({ name: "", email: "", subject: "", message: "" });
      }, 3000);
    } catch {
      const mailtoLink = `mailto:support@agriai.com?subject=${encodeURIComponent(formData.subject)}&body=${encodeURIComponent(`From: ${formData.name} (${formData.email})\n\n${formData.message}`)}`;
      window.location.href = mailtoLink;
      setSubmitted(true);
      setTimeout(() => {
        setSubmitted(false);
        setFormData({ name: "", email: "", subject: "", message: "" });
      }, 3000);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-50 to-green-50/30">      <nav className="fixed top-0 w-full glass border-b border-gray-200/50 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-linear-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-xl">🌾</span>
          </div>
          <span className="text-xl font-bold gradient-text">AgriAI</span>
        </Link>
        <Link
          to="/login"
          className="text-gray-700 hover:text-green-600 font-medium"
        >
          Login
        </Link>
      </div>
    </nav>      <div className="pt-24 pb-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-gray-900 mb-4">
              Get in Touch
            </h1>
            <p className="text-xl text-gray-600">
              We'd love to hear from you. Send us a message!
            </p>
          </div>

          <div className="grid lg:grid-cols-2 gap-12">            <div className="bg-white rounded-2xl shadow-xl p-8">
            {submitted ? (
              <div className="text-center py-12">
                <CheckCircle
                  size={64}
                  className="text-green-600 mx-auto mb-4"
                />
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Message Sent!
                </h3>
                <p className="text-gray-600">
                  We'll get back to you within 24 hours.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                    placeholder="Full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Subject *
                  </label>
                  <select
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition"
                  >
                    <option value="">Select a subject</option>
                    <option value="general">General Inquiry</option>
                    <option value="support">Technical Support</option>
                    <option value="sales">Sales Question</option>
                    <option value="partnership">Partnership</option>
                    <option value="feedback">Feedback</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Message *
                  </label>
                  <textarea
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent outline-none transition resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-emerald-900 hover:bg-emerald-800 text-white px-6 py-4 rounded-xl font-semibold hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Sending...
                    </>
                  ) : (
                    <>
                      <Send size={20} />
                      Send Message
                    </>
                  )}
                </button>
              </form>
            )}
          </div>            <div className="space-y-8">
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-linear-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center">
                    <Mail className="text-white" size={24} />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">Email Us</h3>
                    <p className="text-gray-600">support@agri-ai.com</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500">
                  We typically respond within 24 hours
                </p>
              </div>

              <div className="bg-white rounded-2xl shadow-xl p-8">
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-12 h-12 bg-linear-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center">
                    <MessageSquare className="text-white" size={24} />
                  </div>
                  <div>
                    <h3 className="font-bold text-gray-900">WhatsApp</h3>
                    <p className="text-gray-600">+1 (555) 123-4567</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500">
                  Quick support via WhatsApp (Mon-Fri, 9AM-6PM)
                </p>
              </div>

              <div className="bg-linear-to-br from-green-50 to-blue-50 rounded-2xl p-8 border border-green-200">
                <h3 className="text-xl font-bold text-gray-900 mb-4">
                  Need Immediate Help?
                </h3>
                <p className="text-gray-600 mb-6">
                  Check out our documentation for quick answers
                </p>
                <Link
                  to="/docs"
                  className="inline-block bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition"
                >
                  Browse Docs
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
