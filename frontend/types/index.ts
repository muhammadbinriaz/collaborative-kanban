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

export type WorkspaceDetail = Workspace & {
  members: {
    id: string;
    user_id: string;
    role: WorkspaceRole;
    name: string;
    email: string;
  }[];
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
