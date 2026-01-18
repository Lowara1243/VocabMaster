import React, { useState, useEffect } from 'react';
import WordForm from './components/WordForm.jsx';
import Results from './components/Results.jsx';
import History from './components/History.jsx';
import { languages } from './components/languages';
import { parseCsvLine, createCsvLine, unformatExample, splitByCommaRespectingBrackets } from './utils';

const API_URL = import.meta.env.VITE_APP_API_URL || 'http://127.0.0.1:8000/process-words';

function App() {
  const [text, setText] = useState('');
  const [results, setResults] = useState([]);
  const [history, setHistory] = useState(() => {
    try {
      const savedHistory = localStorage.getItem('wordHistory');
      return savedHistory ? JSON.parse(savedHistory) : [];
    } catch (error) {
      console.error("Failed to load history from localStorage:", error);
      return [];
    }
  });
  const [sourceLang, setSourceLang] = useState(() => localStorage.getItem('sourceLang') || 'English');
  const [targetLang, setTargetLang] = useState(() => localStorage.getItem('targetLang') || 'Russian');

  // Save state to localStorage
  useEffect(() => {
    try {
      localStorage.setItem('wordHistory', JSON.stringify(history));
      localStorage.setItem('wordText', text);
      localStorage.setItem('sourceLang', sourceLang);
      localStorage.setItem('targetLang', targetLang);
    } catch (error) {
      console.error("Failed to save to localStorage:", error);
    }
  }, [history, text, sourceLang, targetLang]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;

    // Use smart splitting that respects brackets
    const words = Array.from(new Set(splitByCommaRespectingBrackets(text).map(w => w.trim().toLowerCase()).filter(w => w)));
    const newResults = words.map(word => ({
      originalWord: word,
      word: word,
      status: 'processing'
    }));

    setResults(prev => [...newResults, ...prev.filter(p => !words.includes(p.originalWord))]);
    setText('');

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: words.join(','),
          source_lang: sourceLang,
          target_lang: targetLang
        }),
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const processLine = (line) => {
        if (!line.trim()) return;
        const parsedResult = parseCsvLine(line);
        if (parsedResult) {
          setResults(prevResults => {
            const updatedResults = prevResults.map(r => {
              if (r.originalWord === parsedResult.originalWord) {
                if (parsedResult.transcription === '[error]') {
                  return { ...r, status: 'error', error: parsedResult.word };
                }
                const isNotFound = parsedResult.transcription === 'N/A';
                if (!isNotFound) {
                  setHistory(prevHistory => {
                    const historyWords = new Set(prevHistory.map(item => item.word));
                    if (!historyWords.has(parsedResult.word)) {
                      return [parsedResult, ...prevHistory];
                    }
                    return prevHistory;
                  });
                }
                return { ...parsedResult, status: isNotFound ? 'not_found' : 'completed' };
              }
              return r;
            });
            return updatedResults;
          });
        }
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          processLine(line);
        }
      }

      // Process any remaining buffer
      if (buffer.trim()) {
        processLine(buffer);
      }
    } catch (error) {
      console.error("Processing error:", error);
      // Mark all processing words as error
      setResults(prevResults =>
        prevResults.map(r =>
          words.includes(r.originalWord) ? { ...r, status: 'error', error: error.message } : r
        )
      );
    }
  };

  const handleDownload = () => {
    if (history.length === 0) {
      alert("History is empty. Nothing to download.");
      return;
    }

    const csvData = history.map(item => {
      const row = [
        item.word || '',          // Word
        item.transcription || '', // Transcription
        item.translation || '',   // Translation
      ];

      // Add all examples as pairs starting from index 3
      if (item.examples && item.examples.length > 0) {
        item.examples.forEach(ex => {
          row.push(unformatExample(ex.source) || '');
          row.push(unformatExample(ex.translation) || '');
        });
      }

      return createCsvLine(row);
    }).join('\n');

    const blob = new Blob(['\uFEFF' + csvData], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', 'word_history.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleClearHistory = () => {
    if (window.confirm("Are you sure you want to clear the entire history? This cannot be undone.")) {
      setHistory([]);
    }
  };

  return (
    <div className="container mt-5">
      <header className="text-center mb-5">
        <h1>Word Processor</h1>
        <p className="lead">Enter comma-separated words, phrases, or sentences to get their translations and examples.</p>
      </header>

      <WordForm
        text={text}
        setText={setText}
        handleSubmit={handleSubmit}
        sourceLang={sourceLang}
        setSourceLang={setSourceLang}
        targetLang={targetLang}
        setTargetLang={setTargetLang}
        languages={languages}
      />

      <Results results={results} />

      <History
        history={history}
        handleDownload={handleDownload}
        handleClearHistory={handleClearHistory}
      />

      <footer className="text-center mt-5 text-muted">
        <p>Powered by Gemini</p>
      </footer>
    </div>
  );
}

export default App;
