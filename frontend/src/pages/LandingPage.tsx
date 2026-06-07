import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useWebVitals } from "../hooks/useWebVitals";
import {
  ArrowRight,
  CheckCircle,
  Cloud,
  TrendingUp,
  Brain,
  Shield,
  Zap,
  ChevronDown,
  ChevronUp,
  FileText,
  BookOpen,
  Mail,
  HelpCircle,
  Send,
  Twitter,
  Linkedin,
  Github,
  Menu,
  X,
} from "lucide-react";

export const LandingPage: React.FC = () => {
  // Monitor Web Vitals in production
  useWebVitals();

  // Track scroll for navbar shrink effect
  const [isScrolled, setIsScrolled] = useState(false);

  // Track active section for link highlighting
  const [activeSection, setActiveSection] = useState("");

  // Track billing period (monthly/annual)
  const [billingPeriod, setBillingPeriod] = useState<"monthly" | "annual">(
    "monthly"
  );

  // Track open FAQ items
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(0);

  // Track dropdown states
  const [productsOpen, setProductsOpen] = useState(false);
  const [resourcesOpen, setResourcesOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    // Smooth scroll behavior
    document.documentElement.style.scrollBehavior = "smooth";

    const handleScroll = () => {
      // Shrink navbar after 50px scroll
      setIsScrolled(window.scrollY > 50);

      // Detect active section
      const sections = ["features", "pricing"];
      const scrollPosition = window.scrollY + 100;

      for (const section of sections) {
        const element = document.getElementById(section);
        if (element) {
          const { offsetTop, offsetHeight } = element;
          if (
            scrollPosition >= offsetTop &&
            scrollPosition < offsetTop + offsetHeight
          ) {
            setActiveSection(section);
            return;
          }
        }
      }
      setActiveSection("");
    };

    window.addEventListener("scroll", handleScroll);
    return () => {
      window.removeEventListener("scroll", handleScroll);
      document.documentElement.style.scrollBehavior = "auto";
    };
  }, []);

  return (
    <div className="min-h-screen bg-white">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-6 focus:py-3 bg-[#1B5E20] text-white font-semibold rounded-lg shadow-lg"
      >
        Skip to main content
      </a>
      <nav
        className={`fixed top-0 w-full bg-white border-b border-[#DDE2E0] z-50 transition-all duration-300 ${isScrolled ? "shadow-[0_2px_8px_rgba(0,0,0,0.05)]" : ""
          }`}
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="max-w-7xl mx-auto px-6">
          <div
            className={`flex items-center justify-between transition-all duration-300 ${isScrolled ? "h-16" : "h-20"
              }`}
          >
            {" "}
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 flex items-center justify-center transition-all">
                <span className="text-2xl">🌾</span>
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-semibold text-[#0A0D0B] leading-tight tracking-tight">
                  AgriAI
                </span>
                <span className="text-xs text-[#3B423F] font-medium leading-tight">
                  Smart Farming Platform
                </span>
              </div>
            </Link>{" "}
            <div className="hidden lg:flex items-center gap-1 bg-[#F4F6F5] rounded-full px-2 py-2">
              {" "}
              <div
                className="relative"
                onMouseEnter={() => setProductsOpen(true)}
                onMouseLeave={() => setProductsOpen(false)}
              >
                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-white rounded-full transition-all duration-200 flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-1">
                  Products
                  <ChevronDown
                    size={14}
                    className={`transition-transform duration-200 ${productsOpen ? "rotate-180" : ""
                      }`}
                  />
                </button>
                {productsOpen && (
                  <div className="absolute top-full left-0 mt-2 w-64 bg-white rounded-lg shadow-[0_4px_16px_rgba(0,0,0,0.08)] border border-[#DDE2E0] py-2 z-50 animate-fadeIn">
                    <Link
                      to="/dashboard/agent"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <Brain size={20} className="text-purple-600" />
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          AI Advisor
                        </div>
                        <div className="text-xs text-gray-500">
                          Smart recommendations
                        </div>
                      </div>
                    </Link>
                    <Link
                      to="/dashboard/weather"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <Cloud size={20} className="text-blue-600" />
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          Weather Intelligence
                        </div>
                        <div className="text-xs text-gray-500">
                          Accurate forecasts
                        </div>
                      </div>
                    </Link>
                    <Link
                      to="/dashboard/prices"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <TrendingUp size={20} className="text-green-600" />
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          Price Tracking
                        </div>
                        <div className="text-xs text-gray-500">
                          Market insights
                        </div>
                      </div>
                    </Link>
                    <Link
                      to="/dashboard/yield-prediction"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <Zap size={20} className="text-yellow-600" />
                      <div>
                        <div className="text-sm font-semibold text-gray-900">
                          Yield Prediction
                        </div>
                        <div className="text-xs text-gray-500">
                          Forecast harvest
                        </div>
                      </div>
                    </Link>
                    <div className="border-t border-gray-100 mt-2 pt-2">
                      <a
                        href="#features"
                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-green-600 hover:bg-green-50 transition-colors"
                      >
                        View All Features
                        <ArrowRight size={14} />
                      </a>
                    </div>
                  </div>
                )}
              </div>{" "}
              <a
                href="#features"
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-1 ${activeSection === "features"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-700 hover:text-gray-900 hover:bg-white"
                  }`}
              >
                Features
              </a>{" "}
              <a
                href="#pricing"
                className={`px-4 py-2 text-sm font-medium rounded-full transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-1 ${activeSection === "pricing"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-700 hover:text-gray-900 hover:bg-white"
                  }`}
              >
                Pricing
              </a>{" "}
              <div
                className="relative"
                onMouseEnter={() => setResourcesOpen(true)}
                onMouseLeave={() => setResourcesOpen(false)}
              >
                <button className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-white rounded-full transition-all duration-200 flex items-center gap-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:ring-offset-1">
                  Resources
                  <ChevronDown
                    size={14}
                    className={`transition-transform duration-200 ${resourcesOpen ? "rotate-180" : ""
                      }`}
                  />
                </button>
                {resourcesOpen && (
                  <div className="absolute top-full left-0 mt-2 w-56 bg-white rounded-xl shadow-xl border border-gray-100 py-2 z-50 animate-fadeIn">
                    <Link
                      to="/docs"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <BookOpen size={18} className="text-blue-600" />
                      <div className="text-sm font-semibold text-gray-900">
                        Documentation
                      </div>
                    </Link>
                    <Link
                      to="/blog"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <FileText size={18} className="text-purple-600" />
                      <div className="text-sm font-semibold text-gray-900">
                        Blog
                      </div>
                    </Link>
                    <Link
                      to="/contact"
                      className="flex items-center gap-3 px-4 py-3 hover:bg-gray-50 transition-colors"
                    >
                      <Mail size={18} className="text-green-600" />
                      <div className="text-sm font-semibold text-gray-900">
                        Contact
                      </div>
                    </Link>
                  </div>
                )}
              </div>
            </div>{" "}
            <div className="hidden md:flex items-center gap-3">
              <Link
                to="/login"
                className="px-5 py-2 text-sm font-semibold text-gray-700 hover:text-gray-900 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-green-500 focus-visible:rounded-lg"
              >
                Sign in
              </Link>
              <Link
                to="/register"
                className="px-6 py-2.5 bg-[#1B5E20] hover:bg-[#124218] text-white text-sm font-semibold rounded-full shadow-[0_2px_8px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1B5E20] focus-visible:ring-offset-2 flex items-center gap-2"
              >
                Get Started
                <ArrowRight
                  size={16}
                  className="group-hover:translate-x-0.5 transition-transform"
                />
              </Link>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 bg-white">
            <div className="px-4 py-4 space-y-3">
              <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg font-medium">Features</a>
              <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg font-medium">Pricing</a>
              <Link to="/docs" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg font-medium">Documentation</Link>
              <Link to="/blog" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg font-medium">Blog</Link>
              <Link to="/contact" onClick={() => setMobileMenuOpen(false)} className="block px-4 py-2 text-gray-700 hover:bg-gray-50 rounded-lg font-medium">Contact</Link>
              <div className="border-t border-gray-200 pt-3 mt-3 space-y-2">
                <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="block w-full text-center px-4 py-2.5 text-gray-700 font-semibold border border-gray-300 rounded-full hover:bg-gray-50">Sign In</Link>
                <Link to="/register" onClick={() => setMobileMenuOpen(false)} className="block w-full text-center px-4 py-2.5 bg-[#1B5E20] text-white font-semibold rounded-full hover:bg-[#124218]">Get Started</Link>
              </div>
            </div>
          </div>
        )}
      </nav>{" "}
      <section
        id="main-content"
        className="relative min-h-screen flex items-center overflow-hidden bg-[#f5fdf8] pt-36 pb-40"
        role="main"
        aria-label="Hero section"
      >
        {" "}
        <div className="absolute inset-0 w-full h-full">
          {" "}
          <picture>
            <source
              media="(max-width: 480px)"
              srcSet="/images/optimized/image-480w.webp"
              type="image/webp"
            />
            <source
              media="(max-width: 768px)"
              srcSet="/images/optimized/image-768w.webp"
              type="image/webp"
            />
            <source
              media="(max-width: 1400px)"
              srcSet="/images/optimized/image-1400w.webp"
              type="image/webp"
            />
            <source
              srcSet="/images/optimized/image-1920w.webp"
              type="image/webp"
            />
            <img
              src="/images/image.png"
              alt="Farmers working in agricultural fields with modern farming equipment and lush green crops"
              className="absolute bottom-0 left-0 w-full h-auto min-h-[120%] object-cover opacity-30"
              style={{ objectPosition: "center bottom" }}
              loading="eager"
              fetchPriority="high"
              decoding="async"
            />
          </picture>{" "}
          <div className="absolute inset-0 bg-[#F4F6F5]/80"></div>{" "}
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "radial-gradient(circle at 1px 1px, rgba(46, 125, 50, 0.05) 1px, transparent 0)",
              backgroundSize: "40px 40px",
            }}
          ></div>
        </div>
        <div className="max-w-7xl mx-auto text-center w-full relative z-10 px-4">
          <div className="animate-fadeIn">
            {" "}
            <div className="inline-flex items-center gap-2 bg-white/90 backdrop-blur-sm border border-gray-200 px-4 py-2 rounded-full shadow-sm mb-8">
              <span className="text-lg">🌱</span>
              <span className="text-sm font-semibold text-gray-700">
                Trusted by 10,000+ farmers worldwide
              </span>
            </div>
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-gray-900 mb-6">
              The AI Platform
              <span className="block mt-2 text-[#1B5E20]">for Agriculture</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-800 mb-4 max-w-3xl mx-auto font-medium">
              Turn farm data into actionable intelligence.
            </p>
            <p className="text-lg text-gray-700 mb-10 max-w-2xl mx-auto">
              Predict yields, optimize inputs, and automate scouting with
              production-grade AI agents built for modern farming.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
              <Link
                to="/register"
                className="group bg-[#1B5E20] hover:bg-[#124218] text-white px-8 py-3.5 rounded-lg font-semibold text-base shadow-[0_2px_8px_rgba(0,0,0,0.08)] hover:shadow-[0_4px_12px_rgba(0,0,0,0.12)] transform hover:-translate-y-0.5 transition-all duration-300 flex items-center justify-center gap-2 min-w-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1B5E20] focus-visible:ring-offset-2"
              >
                Schedule Demo
                <ArrowRight
                  size={18}
                  className="group-hover:translate-x-1 transition-transform"
                />
              </Link>
              <Link
                to="/features"
                className="bg-transparent text-gray-900 px-8 py-3.5 rounded-lg font-semibold text-base hover:bg-white/50 transform hover:-translate-y-0.5 transition-all duration-300 border-2 border-gray-300 hover:border-[#1B5E20] min-w-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#1B5E20] focus-visible:ring-offset-2"
              >
                Explore Platform
              </Link>
            </div>{" "}
            <div className="flex flex-wrap justify-center items-center gap-8 text-center">
              <div className="flex items-center gap-2">
                <CheckCircle size={20} className="text-[#1B5E20]" />
                <span className="text-sm font-semibold text-gray-700">
                  95% Prediction Accuracy
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={20} className="text-[#1B5E20]" />
                <span className="text-sm font-semibold text-gray-700">
                  30% Yield Increase
                </span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle size={20} className="text-[#1B5E20]" />
                <span className="text-sm font-semibold text-gray-700">
                  24/7 AI Monitoring
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>{" "}
      <section id="features" className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Everything You Need to Succeed
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Powerful features designed for modern farmers
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {" "}
            {[
              {
                icon: Brain,
                title: "Smart Crop Advisor",
                description:
                  "Get personalized recommendations for your crops, diseases, and farming decisions in real-time",
                iconColor: "text-purple-600",
                bgColor: "bg-purple-50/50",
              },
              {
                icon: Cloud,
                title: "Precision Weather",
                description:
                  "Accurate forecasts, irrigation planning, and extreme weather alerts tailored to your fields",
                iconColor: "text-blue-500",
                bgColor: "bg-blue-50/50",
              },
              {
                icon: TrendingUp,
                title: "Market Price Alerts",
                description:
                  "Real-time price tracking, trends analysis, and alerts to help you sell at the best time",
                iconColor: "text-[#1B5E20]",
                bgColor: "bg-green-50/50",
              },
              {
                icon: Zap,
                title: "Yield Prediction",
                description:
                  "ML-based forecasts to help you plan better and maximize your harvest potential",
                iconColor: "text-orange-500",
                bgColor: "bg-orange-50/50",
              },
              {
                icon: Shield,
                title: "Disease Detection",
                description:
                  "Upload photos of your crops and get instant AI diagnosis with treatment recommendations",
                iconColor: "text-red-500",
                bgColor: "bg-red-50/50",
              },
              {
                icon: CheckCircle,
                title: "24/7 Monitoring",
                description:
                  "Autonomous AI agent continuously monitors your fields and sends proactive alerts",
                iconColor: "text-teal-600",
                bgColor: "bg-teal-50/50",
              },
            ].map((feature, idx) => (
              <div
                key={idx}
                className="group bg-white rounded-lg p-8 shadow-[0_1px_3px_rgba(0,0,0,0.04)] border border-gray-100 hover:border-[#1B5E20] hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-300 min-h-70 flex flex-col"
              >
                <div
                  className={`w-14 h-14 ${feature.bgColor} rounded-lg flex items-center justify-center mb-6 transition-all duration-300 group-hover:scale-110`}
                >
                  <feature.icon
                    className={feature.iconColor}
                    size={28}
                    strokeWidth={1.5}
                  />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3 leading-tight">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed font-normal text-[15px]">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>{" "}
      <section id="pricing" className="py-20 px-4 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Choose the plan that's right for you
            </p>{" "}
            <div className="flex items-center justify-center gap-4 mb-6">
              <span
                className={`text-base font-medium transition-colors ${billingPeriod === "monthly"
                  ? "text-gray-900"
                  : "text-gray-500"
                  }`}
              >
                Monthly
              </span>
              <button
                onClick={() =>
                  setBillingPeriod(
                    billingPeriod === "monthly" ? "annual" : "monthly"
                  )
                }
                className="relative w-14 h-7 bg-gray-200 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-[#1B5E20] focus:ring-offset-2"
                style={{
                  backgroundColor: billingPeriod === "annual" ? "#1B5E20" : "",
                }}
              >
                <span
                  className="absolute top-0.5 left-0.5 w-6 h-6 bg-white rounded-full shadow-md transition-transform duration-200"
                  style={{
                    transform:
                      billingPeriod === "annual"
                        ? "translateX(28px)"
                        : "translateX(0)",
                  }}
                />
              </button>
              <span
                className={`text-base font-medium transition-colors ${billingPeriod === "annual" ? "text-gray-900" : "text-gray-500"
                  }`}
              >
                Annual
              </span>
              <span className="inline-flex items-center gap-1.5 bg-[#E8F5E9] text-[#1B5E20] text-sm font-semibold px-3 py-1 rounded-full border border-[#1B5E20]/20">
                <span>💰</span> Save 20% with annual billing
              </span>
            </div>
          </div>

          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {" "}
            <div className="bg-white rounded-2xl p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04)] border border-gray-100 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all duration-300">
              {" "}
              <div className="w-14 h-14 bg-[#F6F7F8] rounded-2xl flex items-center justify-center mb-6">
                <span className="text-2xl">🌱</span>
              </div>{" "}
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Free</h3>
              <p className="text-base text-gray-600 mb-6">
                For individual farmers
              </p>{" "}
              <div className="mb-8">
                <div className="flex items-baseline gap-1 mb-8">
                  <span className="text-5xl font-bold text-gray-900">$0</span>
                  <span className="text-gray-600 text-lg">
                    /{billingPeriod === "monthly" ? "month" : "year"}
                  </span>
                </div>{" "}
                <Link
                  to="/register"
                  className="block w-full text-center bg-white border-2 border-gray-300 text-gray-900 px-6 py-3 rounded-xl font-semibold hover:border-gray-400 hover:bg-gray-50 transition-all duration-200"
                >
                  Get Started
                </Link>
              </div>{" "}
              <div className="space-y-3 pt-6 border-t border-gray-100">
                {[
                  "1 Field",
                  "Basic weather forecasts",
                  "Price tracking",
                  "Community support",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <CheckCircle
                      size={18}
                      className="text-gray-400 mt-0.5 shrink-0"
                      strokeWidth={2}
                    />
                    <span className="text-gray-700 text-[15px]">{item}</span>
                  </div>
                ))}
              </div>
            </div>{" "}
            <div className="bg-white rounded-2xl p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04)] border-2 border-[#1B5E20] hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all duration-300 relative">
              {" "}
              <div className="absolute top-6 right-6">
                <span className="bg-[#E8F5E9] text-[#1B5E20] text-xs font-semibold px-3 py-1.5 rounded-full border border-[#1B5E20]/20">
                  Most Popular
                </span>
              </div>{" "}
              <div className="w-14 h-14 bg-[#1B5E20] rounded-2xl flex items-center justify-center mb-6">
                <span className="text-2xl">🚀</span>
              </div>{" "}
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Pro</h3>
              <p className="text-base text-gray-600 mb-6">
                For professional farmers
              </p>{" "}
              <div className="mb-8">
                <div className="flex items-baseline gap-1 mb-2">
                  <span className="text-5xl font-bold text-gray-900">
                    ${billingPeriod === "monthly" ? "29" : "279"}
                  </span>
                  <span className="text-gray-600 text-lg">
                    /{billingPeriod === "monthly" ? "month" : "year"}
                  </span>
                </div>
                {billingPeriod === "annual" && (
                  <p className="text-sm text-gray-500 mb-6">
                    $23.25/month billed annually
                  </p>
                )}
                {billingPeriod === "monthly" && <div className="mb-6" />}{" "}
                <Link
                  to="/register"
                  className="block w-full text-center bg-[#1B5E20] text-white px-6 py-3 rounded-xl font-semibold hover:bg-[#0d3010] transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  Start Free Trial
                </Link>
                <p className="text-xs text-gray-500 text-center mt-3">
                  14-day free trial • No credit card required
                </p>
              </div>{" "}
              <div className="space-y-3 pt-6 border-t border-gray-100">
                {[
                  "Unlimited fields",
                  "AI-powered crop advisor",
                  "Real-time disease detection",
                  "Market price alerts",
                  "AI yield predictions",
                  "Priority support",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <CheckCircle
                      size={18}
                      className="text-[#1B5E20] mt-0.5 shrink-0"
                      strokeWidth={2}
                    />
                    <span className="text-gray-700 text-[15px]">{item}</span>
                  </div>
                ))}
              </div>
            </div>{" "}
            <div className="bg-white rounded-2xl p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04)] border border-gray-100 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all duration-300">
              {" "}
              <div className="w-14 h-14 bg-[#F6F7F8] rounded-2xl flex items-center justify-center mb-6">
                <span className="text-2xl">👥</span>
              </div>{" "}
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Team</h3>
              <p className="text-base text-gray-600 mb-6">
                For agribusiness teams
              </p>{" "}
              <div className="mb-8">
                <div className="flex items-baseline gap-1 mb-8">
                  <span className="text-5xl font-bold text-gray-900">
                    ${billingPeriod === "monthly" ? "99" : "950"}
                  </span>
                  <span className="text-gray-600 text-lg">
                    /{billingPeriod === "monthly" ? "month" : "year"}
                  </span>
                </div>
                {billingPeriod === "annual" && (
                  <p className="text-sm text-gray-500 mb-8">
                    $79.17/month billed annually
                  </p>
                )}{" "}
                <Link
                  to="/contact"
                  className="block w-full text-center bg-white border-2 border-[#1B5E20] text-[#1B5E20] px-6 py-3 rounded-xl font-semibold hover:bg-[#E8F5E9] transition-all duration-200"
                >
                  Contact Sales
                </Link>
              </div>{" "}
              <div className="space-y-3 pt-6 border-t border-gray-100">
                {[
                  "Everything in Pro",
                  "10 team members",
                  "Admin dashboard",
                  "API access",
                  "Custom integrations",
                  "24/7 support",
                ].map((item, idx) => (
                  <div key={idx} className="flex items-start gap-3">
                    <CheckCircle
                      size={18}
                      className="text-gray-400 mt-0.5 shrink-0"
                      strokeWidth={2}
                    />
                    <span className="text-gray-700 text-[15px]">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>{" "}
      <section className="py-20 px-4 bg-[#F9FAFB]">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-14 h-14 bg-[#E8F5E9] rounded-2xl mb-4">
              <HelpCircle
                size={28}
                className="text-[#1B5E20]"
                strokeWidth={2.5}
              />
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Frequently Asked Questions
            </h2>
            <p className="text-lg text-gray-600">
              Everything you need to know about AgriAI
            </p>
          </div>
          <div className="space-y-3">
            {[
              {
                q: "How accurate are the AI predictions?",
                a: "Our AI models are trained on millions of data points and achieve 90%+ accuracy. We continuously improve them with real farmer feedback and the latest agricultural research.",
              },
              {
                q: "Can I use it on my mobile phone?",
                a: "Yes! Our platform is fully responsive and works great on all devices. We also have native mobile apps coming soon for iOS and Android.",
              },
              {
                q: "What if I need help?",
                a: "We offer email support for all users, and priority support for Pro and Team plans. Our community forum is also very active with over 10,000 farmers sharing tips and best practices.",
              },
              {
                q: "Is my data secure?",
                a: "Absolutely. We use industry-standard encryption (AES-256) and never share your data with third parties. Your farm data belongs to you and is stored securely in compliance with international data protection standards.",
              },
              {
                q: "Can I cancel anytime?",
                a: "Yes, you can cancel your subscription at any time with no cancellation fees. No long-term commitments required. If you cancel, you'll continue to have access until the end of your billing period.",
              },
              {
                q: "Do you offer a free trial?",
                a: "Yes! Pro plan comes with a 14-day free trial with no credit card required. You'll get full access to all features so you can see the value firsthand before committing.",
              },
            ].map((faq, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border border-gray-200 overflow-hidden transition-all duration-200 hover:border-gray-300"
              >
                <button
                  onClick={() =>
                    setOpenFaqIndex(openFaqIndex === idx ? null : idx)
                  }
                  className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors duration-150"
                >
                  <h3 className="text-lg font-semibold text-gray-900 pr-8">
                    {faq.q}
                  </h3>
                  <div className="shrink-0">
                    {openFaqIndex === idx ? (
                      <ChevronUp
                        size={20}
                        className="text-[#1B5E20]"
                        strokeWidth={2.5}
                      />
                    ) : (
                      <ChevronDown
                        size={20}
                        className="text-gray-400"
                        strokeWidth={2.5}
                      />
                    )}
                  </div>
                </button>
                <div
                  className={`overflow-hidden transition-all duration-300 ease-in-out ${openFaqIndex === idx
                    ? "max-h-96 opacity-100"
                    : "max-h-0 opacity-0"
                    }`}
                >
                  <div className="px-6 pb-6 pt-0">
                    <p className="text-gray-600 leading-relaxed">{faq.a}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>{" "}
          <div className="mt-12 text-center">
            <p className="text-gray-600 mb-4">Still have questions?</p>
            <Link
              to="/contact"
              className="inline-flex items-center gap-2 text-[#1B5E20] font-semibold hover:underline transition-all"
            >
              Contact our support team
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>{" "}
      <section className="relative py-16 px-4 bg-linear-to-br from-[#1B5E20] via-[#2E7D32] to-[#1B5E20] overflow-hidden">
        {" "}
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                "radial-gradient(circle at 2px 2px, white 1px, transparent 0)",
              backgroundSize: "40px 40px",
            }}
          />
        </div>
        <div className="max-w-4xl mx-auto relative">
          {" "}
          <div className="text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ready to Transform Your Farm?
            </h2>
            <p className="text-lg text-green-50 mb-8 max-w-2xl mx-auto">
              Join thousands of farmers already using AgriAI to increase yields
              and reduce costs
            </p>{" "}
            <div className="max-w-2xl mx-auto mb-8">
              <div className="bg-white/8 backdrop-blur-sm border border-white/10 rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.12)] hover:shadow-[0_12px_48px_rgba(0,0,0,0.16)] transition-all duration-300">
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center shrink-0 shadow-sm">
                    <span className="text-2xl">👨‍🌾</span>
                  </div>
                  <div className="text-left">
                    <p className="text-white italic mb-3 leading-relaxed text-[15px]">
                      "AgriAI helped us increase our yield by 35% in the first
                      season. The AI predictions are incredibly accurate and
                      saved us thousands in input costs."
                    </p>
                    <div>
                      <p className="text-white font-semibold text-sm">
                        Rajesh Kumar
                      </p>
                      <p className="text-green-50/80 text-xs">
                        Organic Farm, Maharashtra • 150 acres
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>{" "}
            <Link
              to="/register"
              className="inline-flex items-center gap-2 bg-white text-[#1B5E20] px-8 py-3.5 rounded-xl font-semibold text-lg shadow-lg hover:shadow-2xl hover:scale-[1.03] transition-all duration-200"
            >
              Start Your Free Trial
              <ArrowRight size={20} />
            </Link>
          </div>
        </div>
      </section>{" "}
      <footer className="bg-gray-900 text-gray-300 py-16 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-12 gap-8 mb-12">
            {" "}
            <div className="md:col-span-4">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-[#1B5E20] rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">🌾</span>
                </div>
                <span className="text-xl font-bold text-white">AgriAI</span>
              </div>
              <p className="text-sm text-gray-400 mb-6 max-w-xs">
                Smart farming solutions powered by AI. Helping farmers make
                data-driven decisions for better yields.
              </p>{" "}
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-white mb-3">
                  Stay Updated
                </h4>
                <div className="flex gap-2">
                  <input
                    type="email"
                    placeholder="Email address"
                    className="flex-1 px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#1B5E20] focus:border-transparent"
                  />
                  <button className="bg-[#1B5E20] text-white p-2 rounded-lg hover:bg-[#0d3010] transition-colors">
                    <Send size={18} />
                  </button>
                </div>
              </div>{" "}
              <div className="flex gap-3">
                <a
                  href="https://twitter.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#1B5E20] transition-colors"
                >
                  <Twitter size={18} />
                </a>
                <a
                  href="https://linkedin.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#1B5E20] transition-colors"
                >
                  <Linkedin size={18} />
                </a>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 bg-gray-800 rounded-lg flex items-center justify-center hover:bg-[#1B5E20] transition-colors"
                >
                  <Github size={18} />
                </a>
              </div>
            </div>{" "}
            <div className="md:col-span-2">
              <h4 className="font-semibold text-white mb-4 text-sm">Product</h4>
              <ul className="space-y-3 text-sm">
                <li>
                  <a
                    href="#features"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Features
                  </a>
                </li>
                <li>
                  <a
                    href="#pricing"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Pricing
                  </a>
                </li>
                <li>
                  <Link
                    to="/docs"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link
                    to="/status"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Status
                  </Link>
                </li>
              </ul>
            </div>{" "}
            <div className="md:col-span-2">
              <h4 className="font-semibold text-white mb-4 text-sm">
                Resources
              </h4>
              <ul className="space-y-3 text-sm">
                <li>
                  <Link
                    to="/blog"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Blog
                  </Link>
                </li>
                <li>
                  <Link
                    to="/docs"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Help Center
                  </Link>
                </li>
                <li>
                  <Link
                    to="/contact"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Support
                  </Link>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Community
                  </a>
                </li>
              </ul>
            </div>{" "}
            <div className="md:col-span-2">
              <h4 className="font-semibold text-white mb-4 text-sm">Company</h4>
              <ul className="space-y-3 text-sm">
                <li>
                  <Link
                    to="/contact"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    About Us
                  </Link>
                </li>
                <li>
                  <Link
                    to="/contact"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Contact
                  </Link>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Careers
                  </a>
                </li>
              </ul>
            </div>{" "}
            <div className="md:col-span-2">
              <h4 className="font-semibold text-white mb-4 text-sm">Legal</h4>
              <ul className="space-y-3 text-sm">
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    Cookie Policy
                  </a>
                </li>
              </ul>
            </div>
          </div>{" "}
          <div className="border-t border-gray-800 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-gray-400">
              © {new Date().getFullYear()} AgriAI Platform. All rights reserved.
            </p>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>Made with ❤️ for farmers</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
