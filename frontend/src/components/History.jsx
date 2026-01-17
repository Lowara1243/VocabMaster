import React from 'react';

// Safe component to render text with <strong> tags
function SafeHtml({ html }) {
  const parts = [];
  let lastIndex = 0;
  const strongRegex = /<strong>(.*?)<\/strong>/g;
  let match;

  while ((match = strongRegex.exec(html)) !== null) {
    // Add text before <strong>
    if (match.index > lastIndex) {
      parts.push(html.slice(lastIndex, match.index));
    }
    // Add <strong> content
    parts.push(<strong key={match.index}>{match[1]}</strong>);
    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < html.length) {
    parts.push(html.slice(lastIndex));
  }

  return <>{parts}</>;
}

function History({ history, handleDownload, handleClearHistory }) {
  return (
    <div className="card">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h5 className="mb-0">History ({history.length} entries)</h5>
        <div>
          <button
            onClick={handleDownload}
            className="btn btn-success btn-sm me-2"
            disabled={history.length === 0}
          >
            Download CSV
          </button>
          <button
            onClick={handleClearHistory}
            className="btn btn-danger btn-sm"
            disabled={history.length === 0}
          >
            Clear History
          </button>
        </div>
      </div>
      <div className="card-body" style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {history.length > 0 ? (
          <ul className="list-group list-group-flush">
            {history.map((item, index) => (
              <li key={index} className="list-group-item">
                <details>
                  <summary className="fw-bold">
                    <strong>{item.word}</strong>
                    {item.translation && <> – <em className="text-muted">{item.translation}</em></>}
                  </summary>
                  <div className="mt-2">
                    <p className="mb-1"><strong>Transcription:</strong> {item.transcription}</p>
                    {item.examples && item.examples.map((ex, exIndex) => (
                      <div key={exIndex} className="mt-2">
                        <p className="mb-1">
                          <strong>Example {exIndex + 1}:</strong> <SafeHtml html={ex.source} />
                        </p>
                        <p className="text-muted">
                          <em><SafeHtml html={ex.translation} /></em>
                        </p>
                      </div>
                    ))}
                  </div>
                </details>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-center text-muted">Your processed entries will appear here.</p>
        )}
      </div>
    </div>
  );
}

export default History;

