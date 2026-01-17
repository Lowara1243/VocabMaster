import { render, screen } from '@testing-library/react';
import Results from './Results';

test('renders results when not empty', () => {
  const results = [{ word: 'test', transcription: '[test]', translation: 'тест', status: 'completed' }];
  render(<Results results={results} />);
  const wordElement = screen.getByText((content, element) => {
    return element.tagName.toLowerCase() === 'strong' && content === 'test';
  });
  expect(wordElement).toBeInTheDocument();
});

test('renders nothing when results are empty', () => {
  const { container } = render(<Results results={[]} />);
  expect(container).toBeEmptyDOMElement();
});
