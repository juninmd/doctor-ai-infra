import { render, screen, fireEvent } from '@testing-library/react';
import { AgentDashboard } from './AgentDashboard';
import '@testing-library/jest-dom';
import { AgentStep } from './ThinkingProcess';

describe('AgentDashboard Component', () => {
  const mockSystemStatus = {
    timestamp: "2026-03-07T12:00:00Z",
    k8s: { status: 'healthy' as const, msg: 'All pods running' },
    gcp: { status: 'healthy' as const, msg: 'APIs ok' },
    gmp: { status: 'healthy' as const, msg: 'Metrics collected' },
    datadog: { status: 'warning' as const, msg: 'High latency detected' },
    azion: { status: 'healthy' as const, msg: 'Edge ok' },
    ai_insight: 'System is stable, but monitoring Datadog latency spikes.'
  };

  it('renders default system status if none provided', () => {
    render(<AgentDashboard steps={[]} />);

    expect(screen.getByText('LIVE STATUS')).toBeInTheDocument();
    const notScannedElements = screen.getAllByText('Not Scanned');
    expect(notScannedElements.length).toBeGreaterThan(0);
  });

  it('renders provided system status', () => {
    render(<AgentDashboard steps={[]} systemStatus={mockSystemStatus} />);

    expect(screen.getByText('All pods running')).toBeInTheDocument();
    expect(screen.getByText('High latency detected')).toBeInTheDocument();
  });

  it('displays the AI insight section when available', () => {
    render(<AgentDashboard steps={[]} systemStatus={mockSystemStatus} />);

    expect(screen.getByText('AI INSIGHT')).toBeInTheDocument();
    expect(screen.getByText('System is stable, but monitoring Datadog latency spikes.')).toBeInTheDocument();
  });

  it('calls onRefresh when refresh button is clicked', () => {
    const handleRefresh = vi.fn();
    render(<AgentDashboard steps={[]} onRefresh={handleRefresh} />);

    const refreshButton = screen.getByTitle('Scan Infrastructure');
    fireEvent.click(refreshButton);

    expect(handleRefresh).toHaveBeenCalledTimes(1);
  });

  it('renders the AgentNetwork visualizer', () => {
    render(<AgentDashboard steps={[]} />);

    expect(screen.getByText('LANGGRAPH AGENT NETWORK')).toBeInTheDocument();
    expect(screen.getByText('SUPERVISOR')).toBeInTheDocument(); // Inside AgentNetwork
  });

  it('passes active agent to AgentNetwork from steps', () => {
    const activeSteps: AgentStep[] = [
      { agent: 'GCP_Specialist', status: 'active', timestamp: Date.now() }
    ];
    render(<AgentDashboard steps={activeSteps} />);

    // AgentNetwork should highlight GCP_Specialist.
    // We check its label has the active color class
    const gcpLabel = screen.getByText('Google Cloud');
    expect(gcpLabel).toHaveClass('text-red-400');
  });
});
