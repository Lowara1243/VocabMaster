import { render, screen } from '@testing-library/react';
import History from './History';

test('renders history', () => {
  const history = [{ word: 'test', translation: 'тест', raw: 'test;[test];тест;;' }];
  render(<History history={history} handleDownload={() => {}} handleClearHistory={() => {}} />);
  const historyElement = screen.getByText(/History \(1 words\)/i);
  expect(historyElement).toBeInTheDocument();
});
