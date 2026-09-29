/** Domain types mirroring the backend's Pydantic schemas. */

export type Role = "client" | "operator" | "admin";

export type RequestStatus = "submitted" | "in_progress" | "delivered" | "accepted" | "rejected";

export type Quality = "good" | "usable" | "bad";

export interface HealthResponse {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
}
