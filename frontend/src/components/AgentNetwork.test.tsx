import { render, screen } from '@testing-library/react';
import { AgentNetwork } from './AgentNetwork';
import { describe, it, expect } from 'vitest';

describe('AgentNetwork Component', () => {
  it('renders correctly with default Supervisor when no agent active', () => {
    render(<AgentNetwork />);

    // Supervisor should be present
    expect(screen.getByText('SUPERVISOR')).toBeInTheDocument();

    // Check for some known agents to be in document
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    expect(screen.getByText('Google Cloud')).toBeInTheDocument();
  });

  it('renders correctly with an active agent', () => {
    // "K8s_Specialist" matches the 'name' property of the Kubernetes agent
    render(<AgentNetwork activeAgent="K8s_Specialist" />);

    // Active agent text
    expect(screen.getByText('Kubernetes')).toBeInTheDocument();
    // It should have the colored class
    const k8sLabel = screen.getByText('Kubernetes');
    expect(k8sLabel).toHaveClass('text-blue-400');
  });

  it('renders all agents in the circle', () => {
    render(<AgentNetwork />);

    // Based on the 'agents' array in AgentNetwork.tsx
    const agentsLabels = [
      "Kubernetes", "Google Cloud", "Datadog", "Traefik", "Azion Edge",
      "Code/Git", "CI/CD", "Security", "Incident", "Automation", "Topology",
      "Planner", "FinOps", "Chaos"
    ];

    agentsLabels.forEach(label => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });
});
