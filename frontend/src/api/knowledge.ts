import { apiClient } from "./client";


export type KnowledgeDocRead = {
  id: number;
  title: string;
  file_name: string;
  file_type: string;
  file_path: string;
  content: string;
  doc_type: string;
  status: string;
  uploaded_by: number;
  error_message: string | null;
  chunks_count: number;
  created_at: string;
  updated_at: string;
};

export type KnowledgeChunkRead = {
  id: number;
  doc_id: number;
  chunk_index: number;
  content: string;
  metadata_json: Record<string, unknown>;
  embedding_id: string | null;
  created_at: string;
  updated_at: string;
};

export type KnowledgeSearchPayload = {
  query: string;
  top_k?: number;
};

export type KnowledgeSearchResult = {
  doc_id: number;
  chunk_id: number;
  chunk_index: number;
  content_preview: string;
  score: number;
  embedding_id: string | null;
};

export async function listKnowledgeDocs() {
  const response = await apiClient.get<KnowledgeDocRead[]>("/knowledge/docs");
  return response.data;
}

export async function getKnowledgeDoc(docId: number) {
  const response = await apiClient.get<KnowledgeDocRead>(`/knowledge/docs/${docId}`);
  return response.data;
}

export async function listKnowledgeChunks(docId: number) {
  const response = await apiClient.get<KnowledgeChunkRead[]>(`/knowledge/docs/${docId}/chunks`);
  return response.data;
}

export async function uploadKnowledgeDoc(payload: { title: string; file: File }) {
  const formData = new FormData();
  formData.append("title", payload.title);
  formData.append("file", payload.file);

  const response = await apiClient.post<KnowledgeDocRead>("/knowledge/upload", formData);
  return response.data;
}

export async function searchKnowledge(payload: KnowledgeSearchPayload) {
  const response = await apiClient.post<KnowledgeSearchResult[]>("/knowledge/search", {
    query: payload.query,
    top_k: payload.top_k ?? 5,
  });
  return response.data;
}
