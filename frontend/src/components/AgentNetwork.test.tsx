import { render, screen } from '@testing-library/react';
import { AgentNetwork } from './AgentNetwork';
import '@testing-library/jest-dom';

describe('AgentNetwork Component', () => {
  it('renders correctly with default Supervisor when no agent active', () => {
    render(<AgentNetwork />);

    // Check if the supervisor text is there
    expect(screen.getByText('SUPERVISOR')).toBeInTheDocument();

    // Check that some of the specific agents are rendered
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('Google Cloud')).toBeInTheDocument();
    expect(screen.getByText('Datadog')).toBeInTheDocument();
  });

  it('renders correctly with an active agent', () => {
    render(<AgentNetwork activeAgent="K8s_Specialist" />);

    // K8s label should be present and highlighted with its active color
    const k8sLabel = screen.getByText('Kubernetes');
    expect(k8sLabel).toBeInTheDocument();
    expect(k8sLabel).toHaveClass('text-blue-400'); // the color associated with K8s_Specialist
  });

  it('renders all agents in the circle', () => {
    render(<AgentNetwork />);

    const agentsLabels = [
      'Kubernetes',
      'Google Cloud',
      'Datadog',
      'Azion Edge',
      'Git / Repo',
      'CI/CD',
      'Security',
    ];

    agentsLabels.forEach(label => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });
});
