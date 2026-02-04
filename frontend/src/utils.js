/**
 * Utility functions for the Word Processor application
 */

/**
 * Split text by comma, respecting brackets [].
 * Commas inside brackets are treated as part of the text, not separators.
 */
export function splitByCommaRespectingBrackets(text) {
  if (!text) return [];

  const parts = [];
  let current = '';
  let bracketDepth = 0;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (char === '[') {
      bracketDepth++;
      current += char;
    } else if (char === ']') {
      if (bracketDepth > 0) bracketDepth--;
      current += char;
    } else if (char === ',' && bracketDepth === 0) {
      parts.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  if (current.trim()) {
    parts.push(current.trim());
  }

  return parts.filter(p => p.length > 0);
}

/**
 * Format example by converting #word# to <strong>word</strong>
 */
export function formatExample(example) {
  if (!example) return '';
  return example.replace(/#([^#]+)#/g, '<strong>$1</strong>');
}

/**
 * Unformat example by converting <strong>word</strong> to #word#
 */
export function unformatExample(example) {
  if (!example) return '';
  return example.replace(/<strong>(.*?)<\/strong>/g, '#$1#');
}

/**
 * Escape double quotes in CSV fields
 */
function escapeQuotes(field) {
  if (field === null || field === undefined) return '';
  const str = String(field);
  if (str.includes('"') || str.includes(';') || str.includes('\n')) {
    return '"' + str.replace(/"/g, '""') + '"';
  }
  return '"' + str + '"';
}

/**
 * Parse a single CSV line with semicolon delimiter
 * Handles quoted fields with semicolons inside
 */
export function parseCsvLine(line) {
  if (!line || !line.trim()) return null;

  const fields = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    const nextChar = line[i + 1];

    if (char === '"') {
      if (inQuotes && nextChar === '"') {
        // Escaped quote
        field += '"';
        i++; // Skip next quote
      } else {
        // Toggle quote mode
        inQuotes = !inQuotes;
      }
    } else if (char === ';' && !inQuotes) {
      // Field separator
      fields.push(field);
      field = '';
    } else {
      field += char;
    }
  }

  // Add last field
  fields.push(field);

  let originalWord = fields[0] || '';
  let displayWord = fields[0] || '';

  // Check for hidden ID field at the end
  // Standard format: Word;Trans;Trn;Ex1;Tr1... (3 + 2N fields = Odd)
  // With ID: Word;Trans;Trn;Ex1;Tr1...;ID (3 + 2N + 1 fields = Even)
  if (fields.length >= 4 && fields.length % 2 === 0) {
    originalWord = fields[fields.length - 1];
    displayWord = fields[0];
    // Remove ID from fields to avoid processing it as an example
    fields.pop();
  }

  // Handle error case
  if (fields.length >= 3 && fields[2].startsWith('[ERROR]:')) {
    return {
      word: originalWord, // The word that caused the error
      transcription: '', // No transcription for an error
      translation: fields[2], // The full error message
      originalWord: originalWord, // The original requested word
      examples: [], // No examples for an error
      status: 'error', // Signal error status to Results.jsx
      raw: line,
    };
  }

  // Handle success case (at least Word;Transcription;Translation)
  if (fields.length >= 3) {
    const examples = [];
    // Examples start from index 3, in pairs (source, translation)
    for (let i = 3; i < fields.length - 1; i += 2) {
      if (fields[i] || fields[i + 1]) {
        examples.push({
          source: formatExample(fields[i] || ''),
          translation: formatExample(fields[i + 1] || '')
        });
      }
    }

    return {
      word: displayWord,                    // The base form (e.g. "liegen")
      transcription: fields[1] || '',       // IPA
      translation: fields[2] || '',         // Translations
      originalWord: originalWord,           // Use hidden ID if present, else same as word
      examples: examples,
      raw: line,
    };
  }

  return null;
}

/**
 * Create CSV line from array of fields
 */
export function createCsvLine(fields) {
  return fields.map(escapeQuotes).join(';');
}

/**
 * Create CSV content from array of rows
 */
export function createCsv(rows) {
  return rows.map(row => createCsvLine(row)).join('\n');
}
