from fastapi.testclient import TestClient


def test_knowledge_upload_and_search_flow(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    upload_response = client.post(
        "/api/knowledge/upload",
        data={"title": "Payment Incident SOP"},
        files={
            "file": (
                "payment_sop.txt",
                b"Payment SOP: verify the gateway callback, order sync status, and retry rules.",
                "text/plain",
            )
        },
        headers=auth_headers,
    )

    assert upload_response.status_code == 200
    uploaded_doc = upload_response.json()
    assert uploaded_doc["title"] == "Payment Incident SOP"
    assert uploaded_doc["status"] == "uploaded"

    doc_id = uploaded_doc["id"]
    detail_response = client.get(f"/api/knowledge/docs/{doc_id}", headers=auth_headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "ready"

    chunks_response = client.get(f"/api/knowledge/docs/{doc_id}/chunks", headers=auth_headers)
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    assert len(chunks) >= 1

    search_response = client.post(
        "/api/knowledge/search",
        json={
            "query": "gateway callback order sync",
            "top_k": 5,
        },
        headers=auth_headers,
    )
    assert search_response.status_code == 200
    results = search_response.json()
    assert len(results) >= 1
    assert results[0]["doc_id"] == doc_id
    assert "gateway callback" in results[0]["content_preview"].lower()
