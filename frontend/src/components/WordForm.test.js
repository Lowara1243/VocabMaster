import { render, screen } from '@testing-library/react';
import WordForm from './WordForm';
import { languages } from './languages';

test('renders word form', () => {
  render(<WordForm text="" setText={() => {}} handleSubmit={() => {}} sourceLang="en" setSourceLang={() => {}} targetLang="ru" setTargetLang={() => {}} languages={languages} />);
  const buttonElement = screen.getByText(/Process Words/i);
  expect(buttonElement).toBeInTheDocument();
  expect(buttonElement).toBeDisabled();
});
