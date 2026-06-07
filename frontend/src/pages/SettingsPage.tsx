import React, { useState } from "react";
import {
  User,
  Bell,
  Shield,
  CreditCard,
  Key,
  AlertTriangle,
  Save,
  Eye,
  EyeOff,
  Mail,
  MessageSquare,
} from "lucide-react";
import { ConfirmDialog } from "../components/ui/ConfirmDialog";
import { useToast } from "../components/ui/Toast";

type Tab = "profile" | "notifications" | "account" | "billing" | "api";

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<Tab>("profile");
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { showToast } = useToast();

  // Profile state
  const [profile, setProfile] = useState({
    name: "John Farmer",
    email: "john@example.com",
    phone: "+91 98765 43210",
    location: "Punjab, India",
    language: "en",
  });

  // Notification settings
  const [notifications, setNotifications] = useState({
    email: true,
    sms: true,
    push: true,
    weatherAlerts: true,
    marketUpdates: true,
    diseaseWarnings: true,
    systemNotifications: false,
    quietHoursEnabled: false,
    quietStart: "22:00",
    quietEnd: "07:00",
  });

  // Account settings
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // Billing state
  const [currentPlan] = useState({
    name: "Pro",
    price: "$29/month",
    nextBilling: "Dec 12, 2025",
  });

  const [invoices] = useState([
    { id: "INV-001", date: "Nov 12, 2025", amount: "$29.00", status: "Paid" },
    { id: "INV-002", date: "Oct 12, 2025", amount: "$29.00", status: "Paid" },
    { id: "INV-003", date: "Sep 12, 2025", amount: "$29.00", status: "Paid" },
  ]);

  // API Keys
  const [apiKeys] = useState([
    {
      id: "1",
      name: "Production API",
      key: "sk_live_*********************xyz",
      created: "Nov 1, 2025",
      lastUsed: "2 hours ago",
    },
    {
      id: "2",
      name: "Development API",
      key: "sk_test_*********************abc",
      created: "Oct 15, 2025",
      lastUsed: "3 days ago",
    },
  ]);

  const handleSaveProfile = () => {
    showToast("Profile saved successfully!", "success");
  };

  const handleSaveNotifications = () => {
    showToast("Notification settings saved!", "success");
  };

  const handleChangePassword = () => {
    if (newPassword !== confirmPassword) {
      showToast("Passwords don't match!", "error");
      return;
    }
    showToast("Password changed successfully!", "success");
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
  };

  const handleDeleteAccount = () => {
    setIsDeleting(true);
    setTimeout(() => {
      showToast("Account deleted. Redirecting...", "success");
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }, 2000);
  };

  const tabs = [
    { id: "profile" as Tab, label: "Profile", icon: User },
    { id: "notifications" as Tab, label: "Notifications", icon: Bell },
    { id: "account" as Tab, label: "Account", icon: Shield },
    { id: "billing" as Tab, label: "Billing", icon: CreditCard },
    { id: "api" as Tab, label: "API Keys", icon: Key },
  ];

  return (
    <div className="min-h-screen bg-linear-to-br from-gray-50 via-green-50/30 to-blue-50/30 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">Settings</h1>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-4 space-y-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl font-semibold transition ${
                    activeTab === tab.id
                      ? "bg-emerald-900 text-white shadow-lg"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}
                >
                  <tab.icon size={20} />
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-2xl shadow-lg p-8">
              {/* Profile Tab */}
              {activeTab === "profile" && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Profile Information
                  </h2>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Full Name
                      </label>
                      <input
                        type="text"
                        value={profile.name}
                        onChange={(e) =>
                          setProfile({ ...profile, name: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Email
                      </label>
                      <input
                        type="email"
                        value={profile.email}
                        onChange={(e) =>
                          setProfile({ ...profile, email: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Phone
                      </label>
                      <input
                        type="tel"
                        value={profile.phone}
                        onChange={(e) =>
                          setProfile({ ...profile, phone: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Location
                      </label>
                      <input
                        type="text"
                        value={profile.location}
                        onChange={(e) =>
                          setProfile({ ...profile, location: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      />
                    </div>

                    <div className="md:col-span-2">
                      <label className="block text-sm font-semibold text-gray-700 mb-2">
                        Language
                      </label>
                      <select
                        value={profile.language}
                        onChange={(e) =>
                          setProfile({ ...profile, language: e.target.value })
                        }
                        className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500 focus:border-transparent"
                      >
                        <option value="en">English</option>
                        <option value="hi">हिन्दी (Hindi)</option>
                        <option value="pa">ਪੰਜਾਬੀ (Punjabi)</option>
                        <option value="es">Español (Spanish)</option>
                      </select>
                    </div>
                  </div>

                  <button
                    onClick={handleSaveProfile}
                    className="flex items-center gap-2 px-6 py-3 bg-emerald-900 hover:bg-emerald-800 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition"
                  >
                    <Save size={18} />
                    Save Changes
                  </button>
                </div>
              )}

              {/* Notifications Tab */}
              {activeTab === "notifications" && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Notification Preferences
                  </h2>

                  {/* Delivery Channels */}
                  <div className="border-b border-gray-200 pb-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Delivery Channels
                    </h3>
                    <div className="space-y-4">
                      {[
                        { key: "email", label: "Email", icon: Mail },
                        { key: "sms", label: "SMS", icon: MessageSquare },
                        {
                          key: "push",
                          label: "Push Notifications",
                          icon: Bell,
                        },
                      ].map((channel) => (
                        <label
                          key={channel.key}
                          className="flex items-center gap-3 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={
                              notifications[
                                channel.key as keyof typeof notifications
                              ] as boolean
                            }
                            onChange={(e) =>
                              setNotifications({
                                ...notifications,
                                [channel.key]: e.target.checked,
                              })
                            }
                            className="w-5 h-5 text-green-600 rounded focus:ring-2 focus:ring-green-500"
                          />
                          <channel.icon size={20} className="text-gray-500" />
                          <span className="font-semibold text-gray-700">
                            {channel.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Alert Types */}
                  <div className="border-b border-gray-200 pb-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Alert Types
                    </h3>
                    <div className="space-y-4">
                      {[
                        { key: "weatherAlerts", label: "Weather Alerts" },
                        { key: "marketUpdates", label: "Market Updates" },
                        { key: "diseaseWarnings", label: "Disease Warnings" },
                        {
                          key: "systemNotifications",
                          label: "System Notifications",
                        },
                      ].map((type) => (
                        <label
                          key={type.key}
                          className="flex items-center gap-3 cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={
                              notifications[
                                type.key as keyof typeof notifications
                              ] as boolean
                            }
                            onChange={(e) =>
                              setNotifications({
                                ...notifications,
                                [type.key]: e.target.checked,
                              })
                            }
                            className="w-5 h-5 text-green-600 rounded focus:ring-2 focus:ring-green-500"
                          />
                          <span className="font-semibold text-gray-700">
                            {type.label}
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  {/* Quiet Hours */}
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Quiet Hours
                    </h3>
                    <label className="flex items-center gap-3 cursor-pointer mb-4">
                      <input
                        type="checkbox"
                        checked={notifications.quietHoursEnabled}
                        onChange={(e) =>
                          setNotifications({
                            ...notifications,
                            quietHoursEnabled: e.target.checked,
                          })
                        }
                        className="w-5 h-5 text-green-600 rounded focus:ring-2 focus:ring-green-500"
                      />
                      <span className="font-semibold text-gray-700">
                        Enable Quiet Hours
                      </span>
                    </label>

                    {notifications.quietHoursEnabled && (
                      <div className="grid grid-cols-2 gap-4 ml-8">
                        <div>
                          <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Start Time
                          </label>
                          <input
                            type="time"
                            value={notifications.quietStart}
                            onChange={(e) =>
                              setNotifications({
                                ...notifications,
                                quietStart: e.target.value,
                              })
                            }
                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-semibold text-gray-700 mb-2">
                            End Time
                          </label>
                          <input
                            type="time"
                            value={notifications.quietEnd}
                            onChange={(e) =>
                              setNotifications({
                                ...notifications,
                                quietEnd: e.target.value,
                              })
                            }
                            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500"
                          />
                        </div>
                      </div>
                    )}
                  </div>

                  <button
                    onClick={handleSaveNotifications}
                    className="flex items-center gap-2 px-6 py-3 bg-emerald-900 hover:bg-emerald-800 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition"
                  >
                    <Save size={18} />
                    Save Preferences
                  </button>
                </div>
              )}

              {/* Account Tab */}
              {activeTab === "account" && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Account Security
                  </h2>

                  {/* Change Password */}
                  <div className="border-b border-gray-200 pb-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Change Password
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Current Password
                        </label>
                        <input
                          type="password"
                          value={currentPassword}
                          onChange={(e) => setCurrentPassword(e.target.value)}
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          New Password
                        </label>
                        <div className="relative">
                          <input
                            type={showPassword ? "text" : "password"}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
                          >
                            {showPassword ? (
                              <EyeOff size={20} />
                            ) : (
                              <Eye size={20} />
                            )}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          value={confirmPassword}
                          onChange={(e) => setConfirmPassword(e.target.value)}
                          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-green-500"
                        />
                      </div>

                      <button
                        onClick={handleChangePassword}
                        className="px-6 py-3 bg-emerald-900 hover:bg-emerald-800 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition"
                      >
                        Update Password
                      </button>
                    </div>
                  </div>

                  {/* Two-Factor Authentication */}
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Two-Factor Authentication
                    </h3>
                    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-xl">
                      <div>
                        <p className="font-semibold text-gray-900">
                          {twoFactorEnabled ? "Enabled" : "Disabled"}
                        </p>
                        <p className="text-sm text-gray-600">
                          Add an extra layer of security to your account
                        </p>
                      </div>
                      <button
                        onClick={() => setTwoFactorEnabled(!twoFactorEnabled)}
                        className={`px-6 py-2 rounded-xl font-semibold transition ${
                          twoFactorEnabled
                            ? "bg-red-100 text-red-700 hover:bg-red-200"
                            : "bg-green-100 text-green-700 hover:bg-green-200"
                        }`}
                      >
                        {twoFactorEnabled ? "Disable" : "Enable"}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Billing Tab */}
              {activeTab === "billing" && (
                <div className="space-y-6">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">
                    Billing & Subscription
                  </h2>

                  {/* Current Plan */}
                  <div className="border-b border-gray-200 pb-6">
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Current Plan
                    </h3>
                    <div className="p-6 bg-linear-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-200">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="text-2xl font-bold text-gray-900">
                            {currentPlan.name}
                          </h4>
                          <p className="text-gray-600">
                            Next billing: {currentPlan.nextBilling}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-3xl font-bold text-green-600">
                            {currentPlan.price}
                          </p>
                        </div>
                      </div>
                      <button className="px-6 py-2 bg-white border border-gray-200 rounded-xl font-semibold hover:bg-gray-50 transition">
                        Change Plan
                      </button>
                    </div>
                  </div>

                  {/* Invoices */}
                  <div>
                    <h3 className="text-lg font-bold text-gray-900 mb-4">
                      Billing History
                    </h3>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-gray-200">
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">
                              Invoice
                            </th>
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">
                              Date
                            </th>
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">
                              Amount
                            </th>
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">
                              Status
                            </th>
                            <th className="text-left py-3 px-4 font-semibold text-gray-700">
                              Action
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {invoices.map((invoice) => (
                            <tr
                              key={invoice.id}
                              className="border-b border-gray-100"
                            >
                              <td className="py-3 px-4 font-mono text-sm">
                                {invoice.id}
                              </td>
                              <td className="py-3 px-4">{invoice.date}</td>
                              <td className="py-3 px-4 font-semibold">
                                {invoice.amount}
                              </td>
                              <td className="py-3 px-4">
                                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-semibold">
                                  {invoice.status}
                                </span>
                              </td>
                              <td className="py-3 px-4">
                                <button className="text-blue-600 font-semibold hover:underline">
                                  Download
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              )}

              {/* API Keys Tab */}
              {activeTab === "api" && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900">
                      API Keys
                    </h2>
                    <button className="px-6 py-3 bg-emerald-900 hover:bg-emerald-800 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition">
                      Create New Key
                    </button>
                  </div>

                  <div className="space-y-4">
                    {apiKeys.map((key) => (
                      <div
                        key={key.id}
                        className="p-6 border border-gray-200 rounded-xl hover:shadow-lg transition"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <h3 className="font-bold text-gray-900 mb-1">
                              {key.name}
                            </h3>
                            <p className="font-mono text-sm text-gray-600">
                              {key.key}
                            </p>
                          </div>
                          <button className="text-red-600 font-semibold hover:underline">
                            Revoke
                          </button>
                        </div>
                        <div className="flex gap-6 text-sm text-gray-600">
                          <span>Created: {key.created}</span>
                          <span>Last used: {key.lastUsed}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="p-6 bg-blue-50 border border-blue-200 rounded-xl">
                    <h3 className="font-bold text-gray-900 mb-2">
                      API Documentation
                    </h3>
                    <p className="text-gray-600 mb-4">
                      Learn how to integrate our API into your applications
                    </p>
                    <button className="text-blue-600 font-semibold hover:underline">
                      View Documentation →
                    </button>
                  </div>
                </div>
              )}

              {/* Danger Zone (shown on account tab) */}
              {activeTab === "account" && (
                <div className="mt-8 p-6 border-2 border-red-200 bg-red-50 rounded-xl">
                  <div className="flex items-start gap-4">
                    <AlertTriangle
                      className="text-red-600 shrink-0"
                      size={24}
                    />
                    <div className="flex-1">
                      <h3 className="text-lg font-bold text-red-900 mb-2">
                        Danger Zone
                      </h3>
                      <p className="text-red-700 mb-4">
                        Once you delete your account, there is no going back.
                        Please be certain.
                      </p>
                      <button
                        onClick={() => setShowDeleteDialog(true)}
                        className="px-6 py-3 bg-red-600 text-white rounded-xl font-semibold hover:bg-red-700 transition"
                      >
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteAccount}
        title="Delete Account"
        message="This action cannot be undone. All your data, fields, and settings will be permanently deleted."
        confirmText="Delete Forever"
        destructive
        loading={isDeleting}
      />
    </div>
  );
};
