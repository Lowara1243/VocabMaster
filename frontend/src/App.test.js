import { render, screen } from '@testing-library/react';
import App from './App';

test('renders main page title', () => {
  render(<App />);
  const titleElement = screen.getByText(/Word Processor/i);
  expect(titleElement).toBeInTheDocument();
});
