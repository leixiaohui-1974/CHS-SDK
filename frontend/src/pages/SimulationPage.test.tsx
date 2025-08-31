import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SimulationPage from './SimulationPage';
import { useProjectStore } from '../store/projectStore';
import axios from 'axios';

// Mock the zustand store
vi.mock('../store/projectStore');

// Mock axios
vi.mock('axios');

// Mock recharts
vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }) => <div data-testid="recharts-container">{children}</div>,
  LineChart: ({ children }) => <div>{children}</div>,
  CartesianGrid: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  Legend: () => <div />,
  Line: () => <div />,
}));

// Mock WebSocket
const mockWebSocket = {
  onopen: vi.fn(),
  onmessage: vi.fn(),
  onerror: vi.fn(),
  close: vi.fn(),
};
global.WebSocket = vi.fn(() => mockWebSocket) as any;


describe('SimulationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows empty message when no project is loaded', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: null,
    });

    render(<SimulationPage />);
    expect(screen.getByText('Please load a project from the Modeling page first.')).toBeInTheDocument();
  });

  it('renders the simulation controls when a project is loaded', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: { components: {}, topology: {}, config: {}, agents: [] },
    });

    render(<SimulationPage />);
    expect(screen.getByText('Start Simulation')).toBeInTheDocument();
    expect(screen.getByText('Stop Simulation')).toBeInTheDocument();
    expect(screen.getByTestId('recharts-container')).toBeInTheDocument();
  });

  it('enables start button and disables stop button initially', () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: { components: {}, topology: {}, config: {}, agents: [] },
    });

    render(<SimulationPage />);
    expect(screen.getByRole('button', { name: /start simulation/i })).toBeEnabled();
    expect(screen.getByRole('button', { name: /stop simulation/i })).toBeDisabled();
  });

  it('calls start simulation endpoint when start button is clicked', async () => {
    vi.mocked(useProjectStore).mockReturnValue({
      projectConfig: { components: {}, topology: {}, config: {}, agents: [] },
    });

    vi.mocked(axios.post).mockResolvedValue({ data: { session_id: 'test-session' } });

    render(<SimulationPage />);

    fireEvent.click(screen.getByText('Start Simulation'));

    // Wait for the async operations to complete
    await screen.findByText('Start Simulation');

    expect(axios.post).toHaveBeenCalledWith('http://localhost:8000/api/simulations', expect.any(Object));
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws/simulations/test-session');
  });
});
