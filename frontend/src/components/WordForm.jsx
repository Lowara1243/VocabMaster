
import React from 'react';

function WordForm({ text, setText, handleSubmit, sourceLang, setSourceLang, targetLang, setTargetLang, languages }) {
  return (
    <div className="card mb-4">
      <div className="card-body">
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <textarea
              className="form-control"
              rows="3"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="e.g., benevolent, ubiquitous, to give up"
            />
          </div>
          <div className="row mb-3">
            <div className="col-md-6 mb-3">
              <label htmlFor="source-lang" className="form-label">Source Language</label>
              <select id="source-lang" className="form-select" value={sourceLang} onChange={(e) => setSourceLang(e.target.value)}>
                {languages.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
            <div className="col-md-6 mb-3">
              <label htmlFor="target-lang" className="form-label">Target Language</label>
              <select id="target-lang" className="form-select" value={targetLang} onChange={(e) => setTargetLang(e.target.value)}>
                {languages.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
          </div>
          <button type="submit" className="btn btn-primary w-100 mt-3" disabled={!text.trim()}>
            Process
          </button>
        </form>
      </div>
    </div>
  );
}

export default WordForm;

