export type User = {
  id: string;
  email: string;
  name: string;
  created_at: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type WorkspaceRole = "owner" | "admin" | "member" | "viewer";

export type Workspace = {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  role?: WorkspaceRole | null;
};

export type WorkspaceMember = {
  id: string;
  user_id: string;
  role: WorkspaceRole;
  name: string;
  email: string;
};

export type WorkspaceDetail = Workspace & {
  members: WorkspaceMember[];
};

export type Board = {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  position: number;
  created_at: string;
  updated_at: string;
};

export type Label = {
  id: string;
  board_id: string;
  name: string;
  color: string;
};

export type Card = {
  id: string;
  list_id: string;
  title: string;
  description: string | null;
  position: number;
  due_date: string | null;
  assignee_id: string | null;
  assignee: User | null;
  labels: Label[];
  created_at: string;
  updated_at: string;
};

export type BoardList = {
  id: string;
  board_id: string;
  name: string;
  position: number;
  created_at: string;
  updated_at: string;
  cards: Card[];
};

export type BoardDetail = Board & {
  lists: BoardList[];
  labels: Label[];
};

export type Invite = {
  id: string;
  workspace_id: string;
  token: string;
  role: WorkspaceRole;
  expires_at: string;
  created_at: string;
  invite_url?: string | null;
};

export type InvitePreview = {
  workspace_id: string;
  workspace_name: string;
  role: WorkspaceRole;
  expires_at: string;
};

export type Comment = {
  id: string;
  card_id: string;
  author_id: string;
  author: User;
  body: string;
  mentioned_user_ids: string[];
  created_at: string;
  updated_at: string;
};

export type Activity = {
  id: string;
  workspace_id: string;
  board_id: string | null;
  card_id: string | null;
  actor_id: string;
  actor: User;
  action: string;
  summary: string;
  meta?: Record<string, unknown> | null;
  created_at: string;
};

export type AppNotification = {
  id: string;
  type: string;
  title: string;
  body: string;
  link: string | null;
  meta?: Record<string, unknown> | null;
  read_at: string | null;
  created_at: string;
};

export type PresenceUser = {
  id: string;
  name: string;
  email: string;
};
