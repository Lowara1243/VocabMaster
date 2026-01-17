/**
 * Utility functions for the Word Processor application
 */

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

  // The first field is the raw word, the second is now the infinitive/parsed word
  const originalWord = fields[0] || '';

  // Handle error case
  if (fields.length >= 3 && fields[2] === '[error]') {
    return {
      originalWord: originalWord,
      word: fields[1] || 'Unknown error', // The error message is in the second field
      transcription: '[error]',
      translation: '',
      example1_en: '',
      example1_ru: '',
      example2_en: '',
      example2_ru: '',
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
      word: fields[0] || '',                // The base form (e.g. "liegen")
      transcription: fields[1] || '',       // IPA
      translation: fields[2] || '',         // Translations
      originalWord: fields[0] || '',        // Use same as word for matching
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
