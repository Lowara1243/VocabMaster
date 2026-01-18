import { describe, it, expect } from 'vitest';
import { parseCsvLine, createCsvLine, formatExample, unformatExample } from './utils';

describe('Utility Functions', () => {
    describe('formatExample', () => {
        it('should format #word# to strong tags', () => {
            expect(formatExample('I have an #apple#.')).toBe('I have an <strong>apple</strong>.');
        });

        it('should handle empty or null input', () => {
            expect(formatExample('')).toBe('');
            expect(formatExample(null)).toBe('');
        });
    });

    describe('unformatExample', () => {
        it('should convert strong tags back to #word#', () => {
            expect(unformatExample('I have an <strong>apple</strong>.')).toBe('I have an #apple#.');
        });
    });

    describe('CSV Handling', () => {
        const csvLine = '"machen zusammen";"[ˈmaxn̩]";"составлять";"Zwei Euro, #macht zusammen# пять.";"Два евро, #составляет# пять."';

        it('should parse a CSV line correctly', () => {
            const parsed = parseCsvLine(csvLine);
            expect(parsed.word).toBe('machen zusammen');
            expect(parsed.transcription).toBe('[ˈmaxn̩]');
            expect(parsed.translation).toBe('составлять');
            expect(parsed.examples).toHaveLength(1);
            expect(parsed.examples[0].source).toBe('Zwei Euro, <strong>macht zusammen</strong> пять.');
        });

        it('should correctly parse fields that are quoted by the backend', () => {
            // Case derived from user report: "hallo";"[ˈhalo]"...
            const serverLine = '"hallo";"[ˈhalo]";"привет, здравствуйте, алло";"#Hallo#, wie geht es dir?";"#Привет#, как дела?";"Sie sagte #hallo# zu mir.";"Она сказала мне #привет#.";"Am Telefon sagte ich #Hallo#.";"По телефону я сказал #алло#."';
            const parsed = parseCsvLine(serverLine);
            expect(parsed.word).toBe('hallo'); // Should NOT be '"hallo"'
            expect(parsed.transcription).toBe('[ˈhalo]'); // Should NOT be '"[ˈhalo]"'
            expect(parsed.translation).toBe('привет, здравствуйте, алло');
            expect(parsed.examples[0].source).toBe('<strong>Hallo</strong>, wie geht es dir?');
        });

        it('should create a CSV line correctly', () => {
            const fields = ['word', 'trans', 'IPA', 'source', 'target'];
            const line = createCsvLine(fields);
            expect(line).toBe('"word";"trans";"IPA";"source";"target"');
        });

        it('should escape quotes in CSV fields', () => {
            const fields = ['He said "Hi"', 'normal'];
            const line = createCsvLine(fields);
            expect(line).toBe('"He said ""Hi""";"normal"');
        });
    });
});
