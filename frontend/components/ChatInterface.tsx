/**
 * O-Negative - AI Blood Coordination Control Center
 * Complete Dashboard integrating:
 * - Gemini 3.6 Flash Conversational Reasoning
 * - NBTC / NACO RAG Vector Search
 * - Live Blood Banks & Distance Matrix (Phase 1)
 * - Persistent Memory & Reliability Scoring (Phase 3)
 * - Privacy-Safe Notification Dispatcher & Audit Log (Phase 5)
 */

'use client';

import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Heart,
  Activity,
  Shield,
  Phone,
  AlertCircle,
  CheckCircle2,
  Clock,
  MapPin,
  Send,
  RefreshCw,
  Bell,
  Users,
  Building2,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Check,
  X
} from 'lucide-react';

interface ReasoningStep {
  step: string;
  reasoning: string[];
}

interface Message {
  id: string;
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  reasoning?: ReasoningStep[];
  confidence?: number;
  parsed_request?: any;
  eligible_donors?: any[];
  eligible_banks?: any[];
}

interface Bank {
  bank_id: string;
  bank_name: string;
  address: string;
  contact: string;
  distance_km: number;
}

interface Donor {
  donor_id: string;
  blood_group: string;
  approx_location: string;
  availability_status: string;
  last_status_update: string;
  reliability_rate?: number;
  response_count?: number;
}

interface AuditEntry {
  id: string;
  timestamp: string;
  channel: string;
  recipient_type: string;
  phone_display: string;
  status: string;
  message_preview: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ChatInterface() {
  // Navigation & Tabs
  const [activeTab, setActiveTab] = useState<'chat' | 'dispatch' | 'audit'>('chat');
  
  // Chat state
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState('Sonipat');
  const [selectedBloodGroup, setSelectedBloodGroup] = useState('O-');
  const [openReasoningMap, setOpenReasoningMap] = useState<Record<string, boolean>>({});
  
  // Live Data State
  const [banks, setBanks] = useState<Bank[]>([]);
  const [donors, setDonors] = useState<Donor[]>([]);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [isRefreshingData, setIsRefreshingData] = useState(false);

  // Notification Modal / Dispatch Form State
  const [notifyTarget, setNotifyTarget] = useState<'donor' | 'patient' | 'bank'>('donor');
  const [notifyName, setNotifyName] = useState('Alice Sharma');
  const [notifyPhoneLast4, setNotifyPhoneLast4] = useState('3210');
  const [notifyId, setNotifyId] = useState('donor_sonipat_001');
  const [notifyBloodGroup, setNotifyBloodGroup] = useState('O-');
  const [notifyStatusMsg, setNotifyStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [dispatching, setDispatching] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  // Load telemetry and initial data
  const fetchData = async () => {
    setIsRefreshingData(true);
    try {
      const [statusRes, banksRes, donorsRes, auditRes] = await Promise.all([
        axios.get(`${API_URL}/api/system/status`).catch(() => null),
        axios.get(`${API_URL}/api/banks?location=${selectedLocation}`).catch(() => null),
        axios.get(`${API_URL}/api/donors?location=${selectedLocation}`).catch(() => null),
        axios.get(`${API_URL}/api/notifications/audit`).catch(() => null),
      ]);

      if (statusRes) setSystemStatus(statusRes.data);
      if (banksRes && banksRes.data.banks) setBanks(banksRes.data.banks);
      if (donorsRes && donorsRes.data.donors) setDonors(donorsRes.data.donors);
      if (auditRes && auditRes.data.entries) setAuditLog(auditRes.data.entries);
    } catch (err) {
      console.error('Error fetching live telemetry:', err);
    } finally {
      setIsRefreshingData(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, [selectedLocation]);

  // Handle Chat Submit
  const handleSubmit = async (e?: React.FormEvent, customQuery?: string) => {
    if (e) e.preventDefault();
    const queryText = customQuery || input;
    if (!queryText.trim() || loading) return;

    const userMessage: Message = {
      id: `u-${Date.now()}`,
      type: 'user',
      content: queryText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!customQuery) setInput('');
    setLoading(true);

    try {
      const response = await axios.post(`${API_URL}/api/query`, {
        query: queryText,
        location: selectedLocation,
        blood_group: selectedBloodGroup,
        user_type: 'patient',
      });

      const agentMessage: Message = {
        id: `a-${Date.now()}`,
        type: 'agent',
        content: response.data.recommendation,
        timestamp: new Date(),
        reasoning: response.data.reasoning_trail,
        confidence: response.data.confidence,
        parsed_request: response.data.parsed_request,
        eligible_donors: response.data.eligible_donors,
        eligible_banks: response.data.eligible_banks,
      };

      setMessages((prev) => [...prev, agentMessage]);
      // Auto-open reasoning for visibility
      setOpenReasoningMap((prev) => ({ ...prev, [agentMessage.id]: true }));
      fetchData(); // Refresh donor/audit states
    } catch (error: any) {
      console.error('Query error:', error);
      const errorMessage: Message = {
        id: `err-${Date.now()}`,
        type: 'agent',
        content: '⚠️ Unable to connect to O-Negative backend. Please verify that the API server is running on port 8000.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Toggle Donor Status
  const handleToggleDonor = async (donorId: string) => {
    try {
      await axios.post(`${API_URL}/api/donors/toggle`, { donor_id: donorId });
      fetchData();
    } catch (err) {
      console.error('Failed to toggle donor:', err);
    }
  };

  // Send Notification
  const handleSendNotification = async (e: React.FormEvent) => {
    e.preventDefault();
    setDispatching(true);
    setNotifyStatusMsg(null);

    try {
      const res = await axios.post(`${API_URL}/api/notify`, {
        recipient_type: notifyTarget,
        recipient_id: notifyId,
        recipient_name: notifyName,
        phone_last_4: notifyPhoneLast4,
        blood_group: notifyBloodGroup,
        location: selectedLocation,
        bank_info: {
          name: banks[0]?.bank_name || 'Apollo Blood Bank',
          contact: banks[0]?.contact || '0130-2241000',
        },
      });

      if (res.data.success) {
        setNotifyStatusMsg({
          type: 'success',
          text: `Notification successfully dispatched (${res.data.status}) to ${notifyName}!`,
        });
        fetchData();
      } else {
        setNotifyStatusMsg({ type: 'error', text: 'Notification failed to dispatch.' });
      }
    } catch (err: any) {
      setNotifyStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Error connecting to notification service.',
      });
    } finally {
      setDispatching(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-slate-100 antialiased overflow-hidden font-sans">
      {/* TOP TELEMETRY & SYSTEM HEADER */}
      <header className="bg-slate-950/80 backdrop-blur border-b border-slate-800 px-6 py-3 flex flex-wrap items-center justify-between gap-4 z-20">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-rose-600 to-red-500 flex items-center justify-center shadow-lg shadow-red-500/20 ring-1 ring-red-400/30">
            <Heart className="h-5 w-5 text-white fill-white animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-rose-200 bg-clip-text text-transparent">
                O-Negative
              </h1>
              <span className="text-xs px-2 py-0.5 rounded-full bg-red-950/60 text-red-400 border border-red-800/50 font-medium">
                Emergency AI v2.0
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5">
              <span>AI-Driven Blood Coordination & Clinical RAG Engine</span>
            </p>
          </div>
        </div>

        {/* Live System Status Badges */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-ping" />
            <span className="text-slate-300 font-medium">
              API: <span className="text-emerald-400">Online</span>
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <Sparkles className="h-3.5 w-3.5 text-amber-400" />
            <span className="text-slate-300">
              LLM: <span className="text-amber-300 font-medium">{systemStatus?.llm_engine || 'Gemini 3.6 Flash'}</span>
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <Shield className="h-3.5 w-3.5 text-blue-400" />
            <span className="text-slate-300">
              Memory: <span className="text-blue-300 font-medium">{systemStatus?.memory_backend?.toUpperCase() || 'SQLITE'}</span>
            </span>
          </div>

          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800">
            <Bell className="h-3.5 w-3.5 text-purple-400" />
            <span className="text-slate-300">
              Notifications: <span className="text-purple-300 font-medium">{systemStatus?.notification_mode?.toUpperCase() || 'SANDBOX'}</span>
            </span>
          </div>

          <button
            onClick={fetchData}
            title="Refresh telemetry"
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshingData ? 'animate-spin text-red-400' : ''}`} />
          </button>
        </div>
      </header>

      {/* MAIN 3-PANEL INTERFACE */}
      <div className="flex-1 flex overflow-hidden">
        {/* LEFT PANEL: BLOOD BANKS & DONOR ROSTER */}
        <aside className="w-80 lg:w-96 bg-slate-950/40 border-r border-slate-800/80 flex flex-col overflow-hidden hidden md:flex">
          {/* Panel Selector / Filter */}
          <div className="p-4 border-b border-slate-800/60 bg-slate-900/40 space-y-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-rose-500" /> Operational Radar
              </span>
              <div className="flex items-center gap-1.5">
                <select
                  value={selectedBloodGroup}
                  onChange={(e) => setSelectedBloodGroup(e.target.value)}
                  className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-md px-1.5 py-1 focus:outline-none focus:ring-1 focus:ring-red-500"
                  title="Target Blood Group"
                >
                  {['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'].map((bg) => (
                    <option key={bg} value={bg}>{bg}</option>
                  ))}
                </select>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded-md px-2 py-1 focus:outline-none focus:ring-1 focus:ring-red-500"
                >
                  <option value="Sonipat">Sonipat (NCR)</option>
                  <option value="Panipat">Panipat</option>
                  <option value="Delhi">Delhi</option>
                </select>
              </div>
            </div>

            {/* Quick Stats Pill */}
            <div className="grid grid-cols-2 gap-2 text-center text-xs">
              <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="text-lg font-bold text-rose-400">{banks.length}</div>
                <div className="text-slate-400 text-[10px]">Active Banks</div>
              </div>
              <div className="p-2 rounded-lg bg-slate-900/80 border border-slate-800">
                <div className="text-lg font-bold text-emerald-400">
                  {donors.filter((d) => d.availability_status === 'available').length} / {donors.length}
                </div>
                <div className="text-slate-400 text-[10px]">Available Donors</div>
              </div>
            </div>
          </div>

          {/* Scrollable list of Banks and Donors */}
          <div className="flex-1 overflow-y-auto p-4 space-y-5">
            {/* Blood Banks Section */}
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Building2 className="h-3.5 w-3.5 text-blue-400" /> Verified Blood Banks
                </h3>
                <span className="text-[10px] text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">
                  data.gov.in
                </span>
              </div>

              <div className="space-y-2.5">
                {banks.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No registered blood banks in this perimeter.</p>
                ) : (
                  banks.map((bank) => (
                    <div
                      key={bank.bank_id}
                      className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition space-y-1.5 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-xs font-semibold text-slate-200 line-clamp-1">{bank.bank_name}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-blue-950/60 text-blue-300 font-mono shrink-0 border border-blue-800/40">
                          {bank.distance_km.toFixed(1)} km
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 line-clamp-1 flex items-center gap-1">
                        <MapPin className="h-3 w-3 shrink-0 text-slate-400" />
                        {bank.address}
                      </p>
                      <div className="flex items-center justify-between pt-1 border-t border-slate-800/50 text-[11px]">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Phone className="h-3 w-3 text-slate-400" /> {bank.contact}
                        </span>
                        <a
                          href={`tel:${bank.contact}`}
                          className="text-[10px] text-rose-400 hover:text-rose-300 font-medium underline"
                        >
                          Call Direct
                        </a>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Live Donor Roster Section */}
            <div>
              <div className="flex items-center justify-between mb-2.5">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5 text-emerald-400" /> Registered Donors (Live)
                </h3>
                <span className="text-[10px] text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">
                  Memory Ranked
                </span>
              </div>

              <div className="space-y-2">
                {donors.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No donors registered in this area.</p>
                ) : (
                  donors.map((donor) => {
                    const isAvail = donor.availability_status === 'available';
                    const reliability = (donor.reliability_rate ?? 0.5) * 100;
                    return (
                      <div
                        key={donor.donor_id}
                        className={`p-2.5 rounded-xl border transition flex items-center justify-between gap-3 ${
                          isAvail
                            ? 'bg-slate-900/80 border-slate-800 hover:border-emerald-500/30'
                            : 'bg-slate-950/60 border-slate-900 opacity-60'
                        }`}
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className="px-2 py-1 rounded-lg bg-red-950/70 border border-red-800/60 text-red-300 font-bold text-xs font-mono">
                            {donor.blood_group}
                          </span>
                          <div className="min-w-0">
                            <p className="text-xs font-medium text-slate-200 truncate">{donor.donor_id}</p>
                            <p className="text-[10px] text-slate-400 flex items-center gap-1">
                              <span>Reliability:</span>
                              <span className="font-semibold text-amber-400">{reliability.toFixed(0)}%</span>
                              <span className="text-slate-400">({donor.response_count || 0} req)</span>
                            </p>
                          </div>
                        </div>

                        {/* Interactive Toggle */}
                        <button
                          onClick={() => handleToggleDonor(donor.donor_id)}
                          title="Click to toggle availability"
                          className={`px-2 py-1 rounded text-[10px] font-medium transition flex items-center gap-1 ${
                            isAvail
                              ? 'bg-emerald-950/70 text-emerald-300 border border-emerald-800/50 hover:bg-emerald-900'
                              : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                          }`}
                        >
                          {isAvail ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                          {isAvail ? 'Available' : 'Resting'}
                        </button>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        </aside>

        {/* CENTER PANEL: AI COORDINATION & CLINICAL REASONING CHAT */}
        <main className="flex-1 flex flex-col bg-slate-900/60 overflow-hidden relative">
          {/* Tab bar for mobile & quick view */}
          <div className="flex items-center justify-between border-b border-slate-800 px-4 py-2 bg-slate-950/40 text-xs">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab('chat')}
                className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'chat'
                    ? 'bg-rose-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Sparkles className="h-3.5 w-3.5" /> AI Clinical Reasoning
              </button>
              <button
                onClick={() => setActiveTab('dispatch')}
                className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'dispatch'
                    ? 'bg-rose-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Send className="h-3.5 w-3.5" /> Emergency Dispatch
              </button>
              <button
                onClick={() => setActiveTab('audit')}
                className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
                  activeTab === 'audit'
                    ? 'bg-rose-600 text-white shadow'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                <Clock className="h-3.5 w-3.5" /> Audit Trail ({auditLog.length})
              </button>
            </div>

            <div className="hidden sm:flex items-center gap-2 text-[11px] text-slate-400">
              <span className="flex items-center gap-1">
                <Shield className="h-3 w-3 text-emerald-400" /> NBTC/NACO Verified
              </span>
            </div>
          </div>

          {/* TAB 1: AI CHAT INTERFACE */}
          {activeTab === 'chat' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Message scroll area */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
                {messages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto py-12">
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-tr from-red-600 to-rose-400 flex items-center justify-center mb-4 shadow-xl shadow-red-500/20 ring-4 ring-red-500/10">
                      <Heart className="h-8 w-8 text-white fill-white" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-100 mb-1">O-Negative Clinical Coordinator</h2>
                    <p className="text-sm text-slate-400 mb-6">
                      Coordinating emergency blood requests and evaluating donor eligibility across India with real-time RAG guidelines and persistent memory.
                    </p>

                    {/* Quick suggestion prompt chips */}
                    <div className="w-full space-y-2 text-left">
                      <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider px-1">
                        Try an example clinical inquiry:
                      </p>
                      {[
                        "Can I donate blood if I'm on antibiotics?",
                        "My cousin gave blood a month ago and is on antibiotics right now. Can he donate again?",
                        "I need O- blood urgently in Sonipat. Who can help?",
                        "What is the deferral period after getting a tattoo or piercing?",
                      ].map((prompt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSubmit(undefined, prompt)}
                          className="w-full text-left p-3 rounded-xl bg-slate-950/50 hover:bg-slate-800/80 border border-slate-800 hover:border-red-500/40 text-xs text-slate-300 transition flex items-center justify-between group"
                        >
                          <span className="group-hover:text-slate-100">"{prompt}"</span>
                          <ChevronRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-red-400 transition transform group-hover:translate-x-0.5" />
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map((message) => {
                    const isUser = message.type === 'user';
                    const isReasoningOpen = openReasoningMap[message.id] || false;

                    return (
                      <div
                        key={message.id}
                        className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
                      >
                        {!isUser && (
                          <div className="h-8 w-8 rounded-lg bg-red-600 flex items-center justify-center shrink-0 shadow mt-1">
                            <Heart className="h-4 w-4 text-white fill-white" />
                          </div>
                        )}

                        <div className={`max-w-2xl space-y-2 ${isUser ? 'items-end' : 'items-start'}`}>
                          {/* Main bubble */}
                          <div
                            className={`p-4 rounded-2xl shadow-md text-sm leading-relaxed ${
                              isUser
                                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-tr-none'
                                : 'bg-slate-950 border border-slate-800 text-slate-100 rounded-tl-none'
                            }`}
                          >
                            <div className="whitespace-pre-wrap font-normal">{message.content}</div>

                            {/* Confidence meter */}
                            {!isUser && message.confidence !== undefined && (
                              <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
                                <span className="flex items-center gap-1 text-[11px]">
                                  <Sparkles className="h-3 w-3 text-amber-400" /> Agent Confidence:
                                </span>
                                <span className="font-semibold text-emerald-400 font-mono">
                                  {Math.round(message.confidence * 100)}%
                                </span>
                              </div>
                            )}
                          </div>

                          {/* Collapsible 5-Step Reasoning Trail (for Agent Responses) */}
                          {!isUser && message.reasoning && message.reasoning.length > 0 && (
                            <div className="rounded-xl bg-slate-950/70 border border-slate-800/80 overflow-hidden text-xs">
                              <button
                                onClick={() =>
                                  setOpenReasoningMap((prev) => ({
                                    ...prev,
                                    [message.id]: !isReasoningOpen,
                                  }))
                                }
                                className="w-full px-3 py-2 bg-slate-900/60 hover:bg-slate-900 flex items-center justify-between text-slate-400 hover:text-slate-200 transition font-medium"
                              >
                                <span className="flex items-center gap-2">
                                  <Activity className="h-3.5 w-3.5 text-rose-400" />
                                  5-Step Clinical Reasoning Trail ({message.reasoning.length} steps logged)
                                </span>
                                {isReasoningOpen ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                              </button>

                              {isReasoningOpen && (
                                <div className="p-3 space-y-3 divide-y divide-slate-900">
                                  {message.reasoning.map((step, sidx) => (
                                    <div key={sidx} className={sidx > 0 ? 'pt-2.5' : ''}>
                                      <div className="font-semibold text-rose-300/90 mb-1 flex items-center gap-1.5 capitalize font-mono text-[11px]">
                                        <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                                        Step {sidx + 1}: {step.step.replace(/_/g, ' ')}
                                      </div>
                                      <ul className="space-y-1 pl-3 border-l border-slate-800 text-slate-400 text-[11px]">
                                        {step.reasoning.map((r, ridx) => (
                                          <li key={ridx} className="leading-normal">
                                            {r}
                                          </li>
                                        ))}
                                      </ul>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}

                          <span className="text-[10px] text-slate-400 px-1">
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}

                {loading && (
                  <div className="flex gap-3 items-center">
                    <div className="h-8 w-8 rounded-lg bg-red-600 flex items-center justify-center shrink-0">
                      <Heart className="h-4 w-4 text-white fill-white animate-bounce" />
                    </div>
                    <div className="p-3 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
                      <RefreshCw className="h-3.5 w-3.5 animate-spin text-red-400" />
                      <span>Evaluating NBTC/NACO rules & querying live donor radar...</span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Chat Input Bar */}
              <div className="p-4 border-t border-slate-800 bg-slate-950/60 backdrop-blur">
                <form onSubmit={(e) => handleSubmit(e)} className="flex items-center gap-2 max-w-4xl mx-auto">
                  <div className="flex-1 relative flex items-center">
                    <input
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      placeholder="Ask clinical eligibility (e.g. antibiotics) or request blood (e.g. O- in Sonipat)..."
                      disabled={loading}
                      className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500/60 disabled:opacity-50"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading || !input.trim()}
                    className="px-5 py-3 rounded-xl bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white font-medium text-sm transition shadow-lg shadow-red-600/20 disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <span>Analyze</span>
                    <Send className="h-4 w-4" />
                  </button>
                </form>
                <div className="text-[10px] text-slate-400 text-center mt-2 flex items-center justify-center gap-3">
                  <span>🔒 Privacy-first SHA-256 phone hashing</span>
                  <span>•</span>
                  <span>🩺 NBTC/NACO Medical Deferrals Vector Database</span>
                  <span>•</span>
                  <span>⚡ Powered by Google Gemini 3.6 Flash</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: EMERGENCY DISPATCH MODAL / FORM */}
          {activeTab === 'dispatch' && (
            <div className="flex-1 overflow-y-auto p-6 max-w-xl mx-auto w-full">
              <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-6 shadow-xl">
                <div className="flex items-center gap-3 pb-4 border-b border-slate-800">
                  <div className="h-10 w-10 rounded-xl bg-red-950/80 border border-red-800/50 flex items-center justify-center">
                    <Send className="h-5 w-5 text-red-400" />
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-slate-100">Emergency Notification Dispatcher</h2>
                    <p className="text-xs text-slate-400">
                      Send verified SMS/WhatsApp alerts (Sandbox Mode: console & audit trail, no real charges).
                    </p>
                  </div>
                </div>

                {notifyStatusMsg && (
                  <div
                    className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
                      notifyStatusMsg.type === 'success'
                        ? 'bg-emerald-950/70 border border-emerald-800/60 text-emerald-300'
                        : 'bg-rose-950/70 border border-rose-800/60 text-rose-300'
                    }`}
                  >
                    {notifyStatusMsg.type === 'success' ? (
                      <CheckCircle2 className="h-4 w-4 shrink-0" />
                    ) : (
                      <AlertCircle className="h-4 w-4 shrink-0" />
                    )}
                    <span>{notifyStatusMsg.text}</span>
                  </div>
                )}

                <form onSubmit={handleSendNotification} className="space-y-4 text-xs">
                  <div>
                    <label className="block text-slate-400 mb-1.5 font-medium">Recipient Type</label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['donor', 'patient', 'bank'] as const).map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setNotifyTarget(t)}
                          className={`py-2 px-3 rounded-lg border capitalize font-medium transition ${
                            notifyTarget === t
                              ? 'bg-rose-600/20 border-rose-500 text-rose-300'
                              : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
                          }`}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-slate-400 mb-1 font-medium">Recipient ID</label>
                      <input
                        type="text"
                        value={notifyId}
                        onChange={(e) => setNotifyId(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-red-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-medium">Recipient Name</label>
                      <input
                        type="text"
                        value={notifyName}
                        onChange={(e) => setNotifyName(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-medium">Phone Last 4 Digits</label>
                      <input
                        type="text"
                        value={notifyPhoneLast4}
                        onChange={(e) => setNotifyPhoneLast4(e.target.value)}
                        placeholder="3210"
                        maxLength={4}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 font-mono focus:outline-none focus:ring-1 focus:ring-red-500"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-slate-400 mb-1 font-medium">Blood Group</label>
                      <select
                        value={notifyBloodGroup}
                        onChange={(e) => setNotifyBloodGroup(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                      >
                        {['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+'].map((bg) => (
                          <option key={bg} value={bg}>
                            {bg}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-medium">Target Location</label>
                      <input
                        type="text"
                        value={selectedLocation}
                        onChange={(e) => setSelectedLocation(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:ring-1 focus:ring-red-500"
                      />
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                    <p className="font-semibold text-slate-300">Message Preview:</p>
                    <p className="italic text-slate-400 font-mono text-[10px]">
                      "Hi {notifyName}, we urgently need {notifyBloodGroup} blood in {selectedLocation}. Can you donate? Bank: {banks[0]?.bank_name || 'Apollo Bank'} ({banks[0]?.contact || '0130-2241000'})"
                    </p>
                  </div>

                  <button
                    type="submit"
                    disabled={dispatching}
                    className="w-full py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-medium text-xs transition shadow disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {dispatching ? (
                      <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Send className="h-3.5 w-3.5" />
                    )}
                    <span>Dispatch Alert to {notifyName}</span>
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 3: LIVE NOTIFICATION AUDIT LOG */}
          {activeTab === 'audit' && (
            <div className="flex-1 overflow-y-auto p-6 max-w-4xl mx-auto w-full space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-purple-400" /> Live Audit Trail
                  </h2>
                  <p className="text-xs text-slate-400">
                    Tamper-evident log of all coordination alerts dispatched by O-Negative.
                  </p>
                </div>
                <button
                  onClick={fetchData}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 flex items-center gap-1.5 transition"
                >
                  <RefreshCw className="h-3 w-3" /> Refresh
                </button>
              </div>

              <div className="rounded-xl bg-slate-950 border border-slate-800 overflow-hidden shadow-lg">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-900/80 text-slate-400 uppercase tracking-wider font-semibold border-b border-slate-800">
                      <tr>
                        <th className="px-4 py-3">Timestamp</th>
                        <th className="px-4 py-3">Type</th>
                        <th className="px-4 py-3">Channel</th>
                        <th className="px-4 py-3">Recipient Hash</th>
                        <th className="px-4 py-3">Status</th>
                        <th className="px-4 py-3">Message</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {auditLog.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="px-4 py-8 text-center text-slate-400 italic">
                            No notifications dispatched yet in this session.
                          </td>
                        </tr>
                      ) : (
                        auditLog.map((entry, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40 transition">
                            <td className="px-4 py-3 font-mono text-[11px] text-slate-400 whitespace-nowrap">
                              {new Date(entry.timestamp).toLocaleTimeString()}
                            </td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] capitalize font-medium text-slate-300">
                                {entry.recipient_type}
                              </span>
                            </td>
                            <td className="px-4 py-3 uppercase text-[10px] text-slate-400">{entry.channel}</td>
                            <td className="px-4 py-3 font-mono text-slate-300">{entry.phone_display}</td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/40 text-[10px] font-medium">
                                {entry.status}
                              </span>
                            </td>
                            <td className="px-4 py-3 max-w-xs truncate text-slate-400" title={entry.message_preview}>
                              {entry.message_preview}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
