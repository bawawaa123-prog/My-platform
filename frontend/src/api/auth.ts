import { apiClient } from "./client";


export type UserRead = {
  id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: UserRead;
};

export async function login(payload: {
  email: string;
  password: string;
}): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("/auth/login", payload);
  return response.data;
}

export async function fetchCurrentUser(): Promise<UserRead> {
  const response = await apiClient.get<UserRead>("/auth/me");
  return response.data;
}
