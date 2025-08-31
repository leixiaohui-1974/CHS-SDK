import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import { describe, it, expect, vi } from 'vitest';

// Mock ProjectLoader component
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

    // Check for the title
    expect(screen.getByText('CHS-SDK Dashboard')).toBeInTheDocument();

    // Check for navigation links
    expect(screen.getByText('Modeling')).toBeInTheDocument();
    expect(screen.getByText('Simulation')).toBeInTheDocument();

    // Check for the mocked ProjectLoader
    expect(screen.getByText('ProjectLoader')).toBeInTheDocument();
  });
});
