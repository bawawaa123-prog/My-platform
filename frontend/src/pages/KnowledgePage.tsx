import { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  listKnowledgeDocs,
  searchKnowledge,
  uploadKnowledgeDoc,
  type KnowledgeDocRead,
  type KnowledgeSearchResult,
} from "../api/knowledge";


type UploadFormState = {
  title: string;
  file: File | null;
};

type SearchFormState = {
  query: string;
  top_k: number;
};

const INITIAL_UPLOAD_FORM: UploadFormState = {
  title: "",
  file: null,
};

const INITIAL_SEARCH_FORM: SearchFormState = {
  query: "",
  top_k: 5,
};

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

function buildTitleSuggestion(fileName: string) {
  const lastDotIndex = fileName.lastIndexOf(".");
  if (lastDotIndex <= 0) {
    return fileName;
  }
  return fileName.slice(0, lastDotIndex);
}

export default function KnowledgePage() {
  const [docs, setDocs] = useState<KnowledgeDocRead[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [docsErrorMessage, setDocsErrorMessage] = useState<string | null>(null);

  const [uploadForm, setUploadForm] = useState<UploadFormState>(INITIAL_UPLOAD_FORM);
  const [uploading, setUploading] = useState(false);
  const [uploadErrorMessage, setUploadErrorMessage] = useState<string | null>(null);
  const [uploadSuccessMessage, setUploadSuccessMessage] = useState<string | null>(null);

  const [searchForm, setSearchForm] = useState<SearchFormState>(INITIAL_SEARCH_FORM);
  const [searching, setSearching] = useState(false);
  const [searchErrorMessage, setSearchErrorMessage] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [docsRefreshKey, setDocsRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    let nextRefreshTimer: number | null = null;

    async function loadDocsLoop(showLoading: boolean) {
      if (showLoading) {
        setLoadingDocs(true);
      }
      setDocsErrorMessage(null);

      try {
        const data = await listKnowledgeDocs();
        if (!active) {
          return;
        }

        setDocs(data);

        if (data.some((doc) => PENDING_KNOWLEDGE_STATUSES.has(doc.status))) {
          nextRefreshTimer = window.setTimeout(() => {
            void loadDocsLoop(false);
          }, 2500);
        }
      } catch {
        if (!active) {
          return;
        }
        setDocsErrorMessage("Unable to load knowledge documents right now.");
      } finally {
        if (active && showLoading) {
          setLoadingDocs(false);
        }
      }
    }

    void loadDocsLoop(true);

    return () => {
      active = false;
      if (nextRefreshTimer !== null) {
        window.clearTimeout(nextRefreshTimer);
      }
    };
  }, [docsRefreshKey]);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    setUploadErrorMessage(null);
    setUploadSuccessMessage(null);

    setUploadForm((current) => ({
      title: current.title || (nextFile ? buildTitleSuggestion(nextFile.name) : ""),
      file: nextFile,
    }));
  }

  async function handleUploadSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!uploadForm.file) {
      setUploadErrorMessage("Please choose a .txt or .md file to upload.");
      return;
    }

    setUploading(true);
    setUploadErrorMessage(null);
    setUploadSuccessMessage(null);

    try {
      const createdDoc = await uploadKnowledgeDoc({
        title: uploadForm.title.trim(),
        file: uploadForm.file,
      });

      setDocs((current) => [createdDoc, ...current.filter((item) => item.id !== createdDoc.id)]);
      setUploadForm(INITIAL_UPLOAD_FORM);
      setUploadSuccessMessage(
        "Document uploaded. Background processing has started and this list will refresh automatically.",
      );
      setDocsRefreshKey((current) => current + 1);
    } catch {
      setUploadErrorMessage("Document upload failed. Please confirm the file is UTF-8 txt/md.");
    } finally {
      setUploading(false);
    }
  }

  async function handleSearchSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedQuery = searchForm.query.trim();
    if (!normalizedQuery) {
      setSearchResults([]);
      setSearchErrorMessage("Please enter a search query.");
      return;
    }

    setSearching(true);
    setSearchErrorMessage(null);

    try {
      const results = await searchKnowledge({
        query: normalizedQuery,
        top_k: searchForm.top_k,
      });
      setSearchResults(results);
    } catch {
      setSearchErrorMessage("Knowledge search failed. Please try again in a moment.");
    } finally {
      setSearching(false);
    }
  }

  function getDocTitle(docId: number) {
    return docs.find((doc) => doc.id === docId)?.title ?? `Document #${docId}`;
  }

  function getStatusHint(doc: KnowledgeDocRead) {
    if (doc.error_message) {
      return doc.error_message;
    }

    if (doc.status === "uploaded") {
      return "Queued for background processing.";
    }

    if (doc.status === "processing") {
      return "Parsing, chunking, and indexing in progress.";
    }

    if (doc.status === "ready") {
      return "Document is ready for semantic retrieval.";
    }

    if (doc.status === "failed") {
      return "Background processing failed.";
    }

    return null;
  }

  return (
    <section className="page-stack">
      <div className="section-hero">
        <div>
          <p className="panel-tag">Step 29 · Knowledge</p>
          <h3>Knowledge base operations desk</h3>
          <p>
            Upload SOP and FAQ documents, inspect their chunking output, and test semantic
            retrieval before the RAG workflow consumes them.
          </p>
        </div>
      </div>

      <section className="content-grid content-grid--knowledge">
        <article className="panel">
          <div className="panel-heading">
            <div>
              <p className="panel-tag">Upload</p>
              <h3>Add a knowledge document</h3>
            </div>
          </div>

          <form className="ticket-form" onSubmit={handleUploadSubmit}>
            <label className="field">
              <span>Document title</span>
              <input
                type="text"
                value={uploadForm.title}
                onChange={(event) =>
                  setUploadForm((current) => ({ ...current, title: event.target.value }))
                }
                placeholder="Payment troubleshooting SOP"
                required
              />
            </label>

            <label className="field">
              <span>Knowledge file</span>
              <input
                type="file"
                accept=".txt,.md,text/plain,text/markdown"
                onChange={handleFileChange}
                required
              />
            </label>

            <p className="helper-copy">
              Supported formats: UTF-8 `.txt` and `.md`. Upload returns quickly, then parsing,
              chunking, embedding, and indexing continue in the background.
            </p>

            {uploadErrorMessage ? <p className="form-error">{uploadErrorMessage}</p> : null}
            {uploadSuccessMessage ? <p className="form-success">{uploadSuccessMessage}</p> : null}

            <div className="form-actions">
              <button type="submit" className="primary-button" disabled={uploading}>
                {uploading ? "Uploading..." : "Upload document"}
              </button>
            </div>
          </form>
        </article>

        <article className="panel panel--feature">
          <div className="panel-heading">
            <div>
              <p className="panel-tag">Search</p>
              <h3>Semantic retrieval test bench</h3>
            </div>
          </div>

          <form className="ticket-form" onSubmit={handleSearchSubmit}>
            <label className="field">
              <span>Search query</span>
              <textarea
                value={searchForm.query}
                onChange={(event) =>
                  setSearchForm((current) => ({ ...current, query: event.target.value }))
                }
                placeholder="Example: payment completed but order status did not update"
                rows={4}
                required
              />
            </label>

            <label className="field field--compact">
              <span>Top K</span>
              <select
                value={String(searchForm.top_k)}
                onChange={(event) =>
                  setSearchForm((current) => ({
                    ...current,
                    top_k: Number(event.target.value),
                  }))
                }
              >
                {[3, 5, 8, 10].map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>

            {searchErrorMessage ? <p className="form-error">{searchErrorMessage}</p> : null}

            <div className="form-actions">
              <button type="submit" className="primary-button" disabled={searching}>
                {searching ? "Searching..." : "Run search"}
              </button>
            </div>
          </form>
        </article>
      </section>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Documents</p>
            <h3>Knowledge library inventory</h3>
          </div>
        </div>

        {loadingDocs ? <p className="panel-state">Loading knowledge documents...</p> : null}
        {docsErrorMessage ? <p className="form-error">{docsErrorMessage}</p> : null}
        {!loadingDocs && !docsErrorMessage && docs.length === 0 ? (
          <p className="panel-state">No knowledge documents have been uploaded yet.</p>
        ) : null}
        {!loadingDocs &&
        !docsErrorMessage &&
        docs.some((doc) => PENDING_KNOWLEDGE_STATUSES.has(doc.status)) ? (
          <p className="panel-state">
            Background processing is active. This document list refreshes automatically while
            uploads are being parsed and indexed.
          </p>
        ) : null}

        {!loadingDocs && !docsErrorMessage && docs.length > 0 ? (
          <div className="ticket-table-wrapper">
            <table className="ticket-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Chunks</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <Link to={`/knowledge/${doc.id}`} className="ticket-link">
                        <strong>{doc.title}</strong>
                        <span className="ticket-link__meta">{doc.file_name}</span>
                      </Link>
                    </td>
                    <td>
                      <div className="ticket-cell-stack">
                        <span>{doc.file_type.toUpperCase()}</span>
                        <span className="ticket-link__meta">{toLabel(doc.doc_type)}</span>
                      </div>
                    </td>
                    <td>
                      <div className="ticket-cell-stack">
                        <span className={`badge badge--knowledge-status badge--${doc.status}`}>
                          {toLabel(doc.status)}
                        </span>
                        {getStatusHint(doc) ? (
                          <span className="ticket-link__meta">{getStatusHint(doc)}</span>
                        ) : null}
                      </div>
                    </td>
                    <td>{doc.chunks_count}</td>
                    <td>{formatDateTime(doc.updated_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </article>

      <article className="panel">
        <div className="panel-heading">
          <div>
            <p className="panel-tag">Search Results</p>
            <h3>Chunk retrieval preview</h3>
          </div>
        </div>

        {searchResults.length === 0 ? (
          <p className="panel-state">Run a knowledge search to inspect chunk matches and scores.</p>
        ) : (
          <div className="search-result-grid">
            {searchResults.map((result) => (
              <article key={result.chunk_id} className="search-result-card">
                <div className="search-result-card__header">
                  <div>
                    <strong>{getDocTitle(result.doc_id)}</strong>
                    <span>
                      Doc #{result.doc_id} · Chunk {result.chunk_index}
                    </span>
                  </div>
                  <span className="badge badge--score">
                    Score {result.score.toFixed(3)}
                  </span>
                </div>
                <p>{result.content_preview}</p>
                <Link to={`/knowledge/${result.doc_id}`} className="ghost-link">
                  View document details
                </Link>
              </article>
            ))}
          </div>
        )}
      </article>
    </section>
  );
}
