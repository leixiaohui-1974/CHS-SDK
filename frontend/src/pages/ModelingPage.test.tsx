import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ModelingPage from './ModelingPage';
import { useProjectStore } from '../store/projectStore';

// Mock the zustand store
vi.mock('../store/projectStore');

// Mock reactflow
vi.mock('reactflow', () => ({
  default: (props) => <div data-testid="react-flow" {...props} />,
  Controls: () => <div>Controls</div>,
  MiniMap: () => <div>MiniMap</div>,
  Background: () => <div>Background</div>,
}));

describe('ModelingPage', () => {
  it('shows loading spinner when isLoading is true', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: null,
      isLoading: true,
      error: null,
      loadProject: vi.fn(),
    });

    render(<ModelingPage />);
    expect(screen.getByTestId('loader')).toBeInTheDocument();
  });

  it('shows error message when error is present', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: null,
      isLoading: false,
      error: 'Failed to load project',
      loadProject: vi.fn(),
    });

    render(<ModelingPage />);
    expect(screen.getByText('Error:')).toBeInTheDocument();
    expect(screen.getByText('Failed to load project')).toBeInTheDocument();
  });

  it('shows empty message when no project is loaded', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: null,
      isLoading: false,
      error: null,
      loadProject: vi.fn(),
    });

    render(<ModelingPage />);
    expect(screen.getByText('No project loaded. Please select an example from the header.')).toBeInTheDocument();
  });

  it('renders the main modeling interface when a project is loaded', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: {
        components: { reservoir: {}, gate: {} },
        topology: { nodes: [], links: [] },
        config: {},
        agents: [],
      },
      isLoading: false,
      error: null,
      loadProject: vi.fn(),
    });

    render(<ModelingPage />);

    expect(screen.getByText('Component Library')).toBeInTheDocument();
    expect(screen.getByText('reservoir')).toBeInTheDocument();
    expect(screen.getByText('gate')).toBeInTheDocument();

    expect(screen.getByTestId('react-flow')).toBeInTheDocument();

    expect(screen.getByText('Parameters')).toBeInTheDocument();
    expect(screen.getByText('Click on a node or edge to see its parameters.')).toBeInTheDocument();
  });
});
