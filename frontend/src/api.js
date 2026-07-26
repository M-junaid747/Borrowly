const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

function getTokens() {
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

function setTokens({ access, refresh }) {
  if (access) localStorage.setItem("access_token", access);
  if (refresh) localStorage.setItem("refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken() {
  const { refresh } = getTokens();
  if (!refresh) return null;
  const response = await fetch(`${API_BASE_URL}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) {
    clearTokens();
    return null;
  }
  const data = await response.json();
  setTokens({ access: data.access });
  return data.access;
}

/**
 * Core request helper used by every API call in the app.
 * - Sends JSON bodies automatically unless `formData` is passed.
 * - Attaches the JWT access token when present.
 * - On a 401, tries one silent token refresh, then retries once.
 */
export async function apiRequest(path, { method = "GET", body, formData, auth = true } = {}) {
  const headers = {};
  if (!formData) headers["Content-Type"] = "application/json";

  const { access } = getTokens();
  if (auth && access) headers["Authorization"] = `Bearer ${access}`;

  const doFetch = async (token) => {
    const finalHeaders = { ...headers };
    if (token) finalHeaders["Authorization"] = `Bearer ${token}`;
    return fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: finalHeaders,
      body: formData ? formData : body ? JSON.stringify(body) : undefined,
    });
  };

  let response = await doFetch(access);

  if (response.status === 401 && auth) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      response = await doFetch(newAccess);
    }
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : null;

  if (!response.ok) {
    const message = data ? JSON.stringify(data) : `Request failed with status ${response.status}`;
    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }
  return data;
}

export const api = {
  register: (payload) => apiRequest("/users/register/", { method: "POST", body: payload, auth: false }),
  login: async (username, password) => {
    const data = await apiRequest("/auth/token/", {
      method: "POST",
      body: { username, password },
      auth: false,
    });
    setTokens({ access: data.access, refresh: data.refresh });
    return data;
  },
  me: () => apiRequest("/users/me/"),
  switchRole: (role) => apiRequest("/users/me/role/", { method: "POST", body: { role } }),

  categories: () => apiRequest("/listings/categories/"),
  listings: (query = "") => apiRequest(`/listings/${query}`),
  myListings: () => apiRequest("/listings/mine/"),
  listing: (id) => apiRequest(`/listings/${id}/`),
  createListing: (payload) => apiRequest("/listings/", { method: "POST", body: payload }),
  uploadListingImage: (listingId, file) => {
    const formData = new FormData();
    formData.append("image", file);
    return apiRequest(`/listings/${listingId}/images/`, { method: "POST", formData });
  },
  uploadListingImages: async (listingId, files) => {
    const results = [];
    for (const file of files) {
      // eslint-disable-next-line no-await-in-loop
      results.push(await api.uploadListingImage(listingId, file));
    }
    return results;
  },

  bookings: () => apiRequest("/bookings/"),
  createBooking: (payload) => apiRequest("/bookings/", { method: "POST", body: payload }),
  updateBookingStatus: (id, status) => apiRequest(`/bookings/${id}/`, { method: "PATCH", body: { status } }),
  dummyPay: (bookingId, cardDetails) => apiRequest(`/bookings/${bookingId}/dummy-pay/`, { method: "POST", body: cardDetails }),

  conversation: (listingId, otherUserId) => apiRequest(`/chat/${listingId}/${otherUserId}/`),
  sendMessage: (listingId, otherUserId, body) =>
    apiRequest(`/chat/${listingId}/${otherUserId}/`,
      { method: "POST",
         body: {
            listing: listingId,
            recipient: otherUserId,
            body 
          } }),
  inbox: () => apiRequest("/chat/inbox/"),
  unreadCount: () => apiRequest("/chat/unread-count/"),

  createReview: (payload) => apiRequest("/reviews/", { method: "POST", body: payload }),
  reviewsFor: (userId) => apiRequest(`/reviews/?reviewee=${userId}`),
};
