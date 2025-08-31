import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { describe, it, expect, vi } from 'vitest';

vi.mock('./components/ProjectLoader', () => ({
    default: () => <div>ProjectLoader</div>,
}));

describe('App', () => {
  it('renders the main application layout', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>
    );

    expect(screen.getByText('CHS-SDK Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Modeling')).toBeInTheDocument();
    expect(screen.getByText('Simulation')).toBeInTheDocument();
    expect(screen.getByText('ProjectLoader')).toBeInTheDocument();
  });
});
