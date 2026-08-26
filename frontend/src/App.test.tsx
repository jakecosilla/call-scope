import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from './App';

describe('CallScope Frontend Application', () => {
  it('renders login screen when unauthenticated', () => {
    render(<App />);
    expect(screen.getByText(/CallScope AI/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/evaluator@callscope.ai/i)).toBeInTheDocument();
  });
});
