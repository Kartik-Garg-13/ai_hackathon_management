import { getSession } from "./auth";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const session = getSession();
  const headers = { ...(options.headers || {}) };
  if (session?.auth_token) {
    headers["Authorization"] = `Bearer ${session.auth_token}`;
  }
  const resp = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (!resp.ok) {
    const text = await resp.text();
    let message = text;
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed.detail === "string") message = parsed.detail;
    } catch {
      // not JSON — fall back to raw text
    }
    throw new Error(message || `Request failed (${resp.status})`);
  }
  return resp.json();
}

function hackathonPath(path) {
  const session = getSession();
  if (!session?.hackathon_id) {
    throw new Error("No active hackathon in session — please log in again.");
  }
  return `/api/hackathons/${session.hackathon_id}${path}`;
}

export const api = {
  health: () => request("/api/health"),

  organizerSignup: (payload) =>
    request("/api/auth/organizer/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  organizerLogin: (payload) =>
    request("/api/auth/organizer/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  listMyHackathons: () => request("/api/hackathons"),
  createHackathon: (payload) =>
    request("/api/hackathons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  getHackathon: (hackathonId) => request(`/api/hackathons/${hackathonId}`),
  generateInviteLinks: (hackathonId) =>
    request(`/api/hackathons/${hackathonId}/invite-links/generate`, { method: "POST" }),
  listInviteLinks: (hackathonId) => request(`/api/hackathons/${hackathonId}/invite-links`),

  resolveInvite: (token) => request(`/api/invite/${token}`),
  registerReviewerViaInvite: (token, payload) =>
    request(`/api/invite/${token}/register/reviewer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  registerParticipantViaInvite: (token, payload) =>
    request(`/api/invite/${token}/register/participant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  listOpenHackathons: () => request("/api/hackathons/public"),
  listAllPublicHackathons: () => request("/api/hackathons/public?include_closed=true"),
  registerParticipant: (hackathonId, payload) =>
    request(`/api/hackathons/${hackathonId}/register/participant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  registerMentor: (hackathonId, payload) =>
    request(`/api/hackathons/${hackathonId}/register/mentor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  loginParticipant: (hackathonId, email) =>
    request(`/api/hackathons/${hackathonId}/login/participant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }),
  loginReviewer: (hackathonId, email) =>
    request(`/api/hackathons/${hackathonId}/login/reviewer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    }),

  uploadRegistrations: (file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(hackathonPath("/registrations/upload"), { method: "POST", body: formData });
  },
  listRegistrations: (riskLevel, approvalStatus, name, limit, offset) => {
    const params = new URLSearchParams();
    if (riskLevel) params.set("risk_level", riskLevel);
    if (approvalStatus) params.set("approval_status", approvalStatus);
    if (name) params.set("name", name);
    if (limit) params.set("limit", limit);
    if (offset) params.set("offset", offset);
    const query = params.toString();
    return request(`${hackathonPath("/registrations")}${query ? `?${query}` : ""}`);
  },
  registrationAnalytics: () => request(hackathonPath("/registrations/analytics")),
  getRegistration: (id) => request(hackathonPath(`/registrations/${id}`)),
  reanalyzeRegistrations: () => request(hackathonPath("/registrations/reanalyze"), { method: "POST" }),
  approveRegistration: (id) => request(hackathonPath(`/registrations/${id}/approve`), { method: "POST" }),
  rejectRegistration: (id) => request(hackathonPath(`/registrations/${id}/reject`), { method: "POST" }),

  listReviewers: () => request(hackathonPath("/reviewers")),
  createReviewer: (payload) =>
    request(hackathonPath("/reviewers"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  runAssignment: () => request(hackathonPath("/reviewers/assign"), { method: "POST" }),
  listAssignments: () => request(hackathonPath("/reviewers/assignments")),

  submitScore: (payload) =>
    request(hackathonPath("/scores"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  biasReport: () => request(hackathonPath("/bias/reviewers")),
  flaggedReviewers: () => request(hackathonPath("/bias/flagged")),
  auditLog: () => request(hackathonPath("/audit-log")),
  normalizedScores: (teamId) => request(hackathonPath(`/teams/${teamId}/normalized-scores`)),

  analyzePitch: (teamId, file) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(`${hackathonPath("/pitch/analyze")}?team_id=${teamId}`, { method: "POST", body: formData });
  },
  getPitchReview: (teamId) => request(hackathonPath(`/pitch/${teamId}`)),

  askCopilot: (question) =>
    request("/api/copilot/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),

  logActivity: (payload) =>
    request(hackathonPath("/activity"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  burnoutReport: () => request(hackathonPath("/burnout/teams")),
  flaggedTeams: () => request(hackathonPath("/burnout/flagged")),

  chatHistory: () => request(hackathonPath("/chat/messages")),
  chatWebSocketUrl: () => {
    const session = getSession();
    const wsBase = BASE_URL.replace(/^http/, "ws");
    return `${wsBase}/ws/hackathons/${session.hackathon_id}/chat?token=${session.auth_token}`;
  },

  submitQuery: (payload) =>
    request(hackathonPath("/queries"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),
  listQueries: () => request(hackathonPath("/queries")),
  respondToQuery: (queryId, response) =>
    request(hackathonPath(`/queries/${queryId}/respond`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ response }),
    }),
  rateQuery: (queryId, rating) =>
    request(hackathonPath(`/queries/${queryId}/rate`), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rating }),
    }),
  mentorLeaderboard: () => request(hackathonPath("/mentors/leaderboard")),

  judgeDashboard: () => request(hackathonPath("/judge-dashboard")),

  getMe: () => request(hackathonPath("/me")),

  listTeams: () => request(hackathonPath("/teams")),
  updateTeamLinks: (teamId, payload) =>
    request(hackathonPath(`/teams/${teamId}/links`), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  similarityReport: () => request(hackathonPath("/similarity/report")),

  getWinners: () => request(hackathonPath("/winners")),
  revealWinners: () => request(hackathonPath("/winners/reveal"), { method: "POST" }),

  scanPlagiarism: () => request(hackathonPath("/plagiarism/scan")),
  comparePlagiarism: (teamAId, teamBId) =>
    request(`${hackathonPath("/plagiarism/compare")}?team_a_id=${teamAId}&team_b_id=${teamBId}`, { method: "POST" }),
};
