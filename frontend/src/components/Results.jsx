
import React from 'react';

function Results({ results }) {
  if (results.length === 0) return null;

  return (
    <div className="card">
      <div className="card-header">
        <h5 className="mb-0">Current Results</h5>
      </div>
      <ul className="list-group list-group-flush">
        {results.map((r) => (
          <li key={r.originalWord || r.word} className="list-group-item d-flex justify-content-between align-items-center">
            <span>
              <strong className="fw-bold">{r.word}</strong>
              {r.transcription && <> {r.transcription}</>}
              {r.translation && <> – <em className="text-muted">{r.translation}</em></>}
            </span>
            {r.status === 'processing' && (
              <div className="spinner-border spinner-border-sm" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
            )}
            {r.status === 'error' && (
              <span title={r.error || "An error occurred"} className="text-danger">⚠️ Error</span>
            )}
            {r.status === 'not_found' && (
              <span title="Entry not found or doesn't exist" className="text-warning">❌ Not found</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Results;
