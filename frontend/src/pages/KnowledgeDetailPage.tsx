import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  getKnowledgeDoc,
  listKnowledgeChunks,
  type KnowledgeChunkRead,
  type KnowledgeDocRead,
} from "../api/knowledge";

const PENDING_KNOWLEDGE_STATUSES = new Set(["uploaded", "processing"]);

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function toLabel(value: string) {
  return value
    .split("_")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export default function KnowledgeDetailPage() {
  const params = useParams();
  const docId = Number(params.docId);

  const [doc, setDoc] = useState<KnowledgeDocRead | null>(null);
  const [chunks, setChunks] = useState<KnowledgeChunkRead[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let nextRefreshTimer: number | null = null;

    async function loadDocDetail(showLoading: boolean) {
      if (!Number.isFinite(docId)) {
        setErrorMessage("Invalid document id.");
        setLoading(false);
        return;
      }

      if (showLoading) {
        setLoading(true);
      }
      setErrorMessage(null);

      try {
        const [docData, chunkData] = await Promise.all([
          getKnowledgeDoc(docId),
          listKnowledgeChunks(docId),
        ]);

        if (!active) {
          return;
        }

        setDoc(docData);
        setChunks(chunkData);

        if (PENDING_KNOWLEDGE_STATUSES.has(docData.status)) {
          nextRefreshTimer = window.setTimeout(() => {
            void loadDocDetail(false);
          }, 2500);
        }
      } catch {
        if (!active) {
          return;
        }
        setErrorMessage("Unable to load this knowledge document right now.");
      } finally {
        if (active && showLoading) {
          setLoading(false);
        }
      }
    }

    void loadDocDetail(true);

    return () => {
      active = false;
      if (nextRefreshTimer !== null) {
        window.clearTimeout(nextRefreshTimer);
      }
    };
  }, [docId]);

  function getStatusHint(knowledgeDoc: KnowledgeDocRead) {
    if (knowledgeDoc.error_message) {
      return knowledgeDoc.error_message;
    }

    if (knowledgeDoc.status === "uploaded") {
      return "This upload is queued for background processing.";
    }

    if (knowledgeDoc.status === "processing") {
      return "Parsing, chunking, embedding, and indexing are still running.";
    }

    if (knowledgeDoc.status === "ready") {
      return "This document is ready for retrieval and RAG usage.";
    }

    if (knowledgeDoc.status === "failed") {
      return "Processing failed. Review the error details below.";
    }

    return null;
  }

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Knowledge Detail</p>
          <h3>Document content and chunk breakdown</h3>
          <p>
            Inspect the raw uploaded content, verify chunk segmentation, and confirm the
            document is ready to participate in semantic retrieval.
          </p>
        </div>
        <Link to="/knowledge" className="ghost-button ghost-button--link">
          Back to knowledge
        </Link>
      </div>

      {loading ? (
        <article className="panel">
          <p className="panel-state">Loading knowledge document...</p>
        </article>
      ) : null}
      {errorMessage ? (
        <article className="panel">
          <p className="form-error">{errorMessage}</p>
        </article>
      ) : null}

      {!loading && !errorMessage && doc ? (
        <>
          <section className="content-grid content-grid--detail">
            <article className="panel panel--feature">
              <div className="ticket-detail-header">
                <div>
                  <p className="panel-tag">Document #{doc.id}</p>
                  <h3>{doc.title}</h3>
                </div>
                <span className={`badge badge--knowledge-status badge--${doc.status}`}>
                  {toLabel(doc.status)}
                </span>
              </div>

              <p className="ticket-description">{doc.content}</p>

              <div className="meta-grid">
                <div className="meta-card">
                  <span className="meta-card__label">File</span>
                  <strong>{doc.file_name}</strong>
                  <span>{doc.file_type.toUpperCase()}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Chunks</span>
                  <strong>{doc.chunks_count}</strong>
                  <span>{toLabel(doc.doc_type)}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Uploaded</span>
                  <strong>{formatDateTime(doc.created_at)}</strong>
                  <span>By user #{doc.uploaded_by}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-card__label">Storage</span>
                  <strong>{formatDateTime(doc.updated_at)}</strong>
                  <span className="knowledge-path">{doc.file_path}</span>
                </div>
              </div>

              {PENDING_KNOWLEDGE_STATUSES.has(doc.status) ? (
                <p className="panel-state">
                  Background processing is still running. This page refreshes automatically until
                  the document becomes ready or fails.
                </p>
              ) : null}

              {doc.error_message ? (
                <p className="form-error knowledge-inline-error">{doc.error_message}</p>
              ) : null}
            </article>

            <article className="panel">
              <div className="panel-heading">
                <div>
                  <p className="panel-tag">Overview</p>
                  <h3>Retrieval readiness</h3>
                </div>
              </div>

              <div className="detail-stack">
                <div className="detail-row">
                  <span>Status</span>
                  <strong>{toLabel(doc.status)}</strong>
                </div>
                <div className="detail-row">
                  <span>Processing note</span>
                  <strong>{getStatusHint(doc)}</strong>
                </div>
                <div className="detail-row">
                  <span>Chunk count</span>
                  <strong>{doc.chunks_count}</strong>
                </div>
                <div className="detail-row">
                  <span>Document type</span>
                  <strong>{toLabel(doc.doc_type)}</strong>
                </div>
                <div className="detail-row">
                  <span>Latest update</span>
                  <strong>{formatDateTime(doc.updated_at)}</strong>
                </div>
              </div>
            </article>
          </section>

          <article className="panel">
            <div className="panel-heading">
              <div>
                <p className="panel-tag">Chunks</p>
                <h3>Knowledge chunk breakdown</h3>
              </div>
            </div>

            {chunks.length === 0 ? (
              <p className="panel-state">
                {PENDING_KNOWLEDGE_STATUSES.has(doc.status)
                  ? "Chunks will appear here after background processing completes."
                  : "This document does not have any chunks yet."}
              </p>
            ) : (
              <div className="chunk-list">
                {chunks.map((chunk) => (
                  <article key={chunk.id} className="chunk-card">
                    <div className="chunk-card__header">
                      <strong>Chunk {chunk.chunk_index}</strong>
                      <span>#{chunk.id}</span>
                    </div>

                    <p className="chunk-card__content">{chunk.content}</p>

                    <div className="chunk-card__footer">
                      <span>Embedding: {chunk.embedding_id ?? "Pending"}</span>
                      <span>{formatDateTime(chunk.updated_at)}</span>
                    </div>

                    <pre className="chunk-card__meta">
                      {JSON.stringify(chunk.metadata_json, null, 2)}
                    </pre>
                  </article>
                ))}
              </div>
            )}
          </article>
        </>
      ) : null}
    </section>
  );
}
