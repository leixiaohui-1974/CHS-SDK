import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SimulationPage from './SimulationPage';
import { useProjectStore } from '../store/projectStore';
import { useSimulationStore } from '../store/simulationStore';

// Mock stores
vi.mock('../store/projectStore');
vi.mock('../store/simulationStore');

// Mock child components and libraries
vi.mock('../components/VariableSidebar', () => ({
  default: () => <div data-testid="variable-sidebar" />
}));
vi.mock('../components/ChartCard', () => ({
  default: ({ chart }) => <div data-testid="chart-card">{chart.variables.join(',')}</div>
}));
vi.mock('react-grid-layout', () => ({
  WidthProvider: (component) => component,
  default: ({ children }) => <div data-testid="grid-layout">{children}</div>
}));
vi.mock('reactflow', () => ({
  default: (props) => <div data-testid="react-flow" nodes={JSON.stringify(props.nodes)} edges={JSON.stringify(props.edges)} />,
  Controls: () => <div />,
  MiniMap: () => <div />,
  Background: () => <div />,
}));


describe('SimulationPage', () => {
  let mockProjectStore: any;
  let mockSimulationStore: any;

  beforeEach(() => {
    vi.clearAllMocks();

    mockProjectStore = {
      projectConfig: { output: { variables: ['var1', 'var2'] } },
    };

    mockSimulationStore = {
      startSimulation: vi.fn(),
      stopSimulation: vi.fn(),
      addChart: vi.fn(),
      updateLayouts: vi.fn(),
      isRunning: false,
      isLoading: false,
      charts: [],
      layouts: {},
      data: [],
      availableVariables: ['var1', 'var2'],
      liveNodes: [],
      liveEdges: [],
    };

    vi.mocked(useProjectStore).mockReturnValue(mockProjectStore);
    vi.mocked(useSimulationStore).mockReturnValue(mockSimulationStore);
  });

  it('shows empty message when no project is loaded', () => {
    vi.mocked(useProjectStore).mockReturnValue({ projectConfig: null });
    render(<SimulationPage />);
    expect(screen.getByText('Please load a project from the Modeling page first.')).toBeInTheDocument();
  });

  it('renders the main layout when a project is loaded', () => {
    render(<SimulationPage />);
    expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument();
    expect(screen.getByTestId('variable-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('grid-layout')).toBeInTheDocument();
    expect(screen.getByTestId('react-flow')).toBeInTheDocument();
  });

  it('calls startSimulation when the start button is clicked', () => {
    render(<SimulationPage />);
    fireEvent.click(screen.getByRole('button', { name: /start/i }));
    expect(mockSimulationStore.startSimulation).toHaveBeenCalledWith(mockProjectStore.projectConfig, undefined);
  });

  it('renders the topology with live nodes and edges', () => {
    mockSimulationStore.liveNodes = [{ id: 'n1', position: { x: 0, y: 0 }, data: { label: 'Node 1' } }];
    mockSimulationStore.liveEdges = [{ id: 'e1', source: 'n1', target: 'n2' }];
    vi.mocked(useSimulationStore).mockReturnValue(mockSimulationStore);

    render(<SimulationPage />);
    const reactFlow = screen.getByTestId('react-flow');
    expect(reactFlow).toBeInTheDocument();
    expect(reactFlow.getAttribute('nodes')).toContain('n1');
    expect(reactFlow.getAttribute('edges')).toContain('e1');
  });
});
