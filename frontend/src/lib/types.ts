/** Domain types mirroring the backend's Pydantic schemas. */

export type Role = "client" | "operator" | "admin";

export type RequestStatus = "submitted" | "in_progress" | "delivered" | "accepted" | "rejected";

export type Quality = "good" | "usable" | "bad";

export interface HealthResponse {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
}

export interface User {
  id: number;
  email: string;
  name: string;
  organisation: string | null;
  role: Role;
  is_active: boolean;
}

export const isStaff = (user: Pick<User, "role">) => user.role !== "client";

export interface UserBrief {
  id: number;
  name: string;
  organisation: string | null;
}

export interface StatusEvent {
  from_status: RequestStatus | null;
  to_status: RequestStatus;
  changed_by: UserBrief;
  changed_at: string;
  note: string | null;
}

export interface DatasetRequest {
  id: number;
  client: UserBrief;
  task_name: string;
  episodes_requested: number;
  episodes_assigned: number;
  deadline: string;
  notes: string | null;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
  allowed_transitions: RequestStatus[];
}

export interface DatasetRequestDetail extends DatasetRequest {
  events: StatusEvent[];
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export const STATUS_LABELS: Record<RequestStatus, string> = {
  submitted: "Submitted",
  in_progress: "In progress",
  delivered: "Delivered",
  accepted: "Accepted",
  rejected: "Rejected",
};
