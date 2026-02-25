import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ChatInterface } from './ChatInterface';
import { vi, describe, it, expect, beforeEach } from 'vitest';

// Mock fetch globally
globalThis.fetch = vi.fn();

// Mock MarkdownRenderer to avoid ESM/remark-gfm issues in JSDOM
vi.mock('./MarkdownRenderer', () => ({
  MarkdownRenderer: ({ content }: { content: string }) => <div data-testid="markdown-content">{content}</div>
}));

function createStreamResponse(data: string[]) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      data.forEach(chunk => {
        controller.enqueue(encoder.encode(chunk));
      });
      controller.close();
    }
  });
  return new Response(stream, { headers: { 'Content-Type': 'text/event-stream' } });
}

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly', () => {
    render(<ChatInterface />);
    expect(screen.getByPlaceholderText('Describe the infrastructure issue...')).toBeInTheDocument();
    expect(screen.getByText('Ready to troubleshoot. Describe your incident.')).toBeInTheDocument();
  });

  it('sends a message and displays the response', async () => {
    const streamData = [
      JSON.stringify({ type: 'activity', agent: 'Supervisor' }) + '\n',
      JSON.stringify({ type: 'message', content: 'Checking system...', agent: 'Supervisor' }) + '\n',
      JSON.stringify({ type: 'final' }) + '\n'
    ];

    (globalThis.fetch as any).mockResolvedValueOnce(createStreamResponse(streamData));

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('Describe the infrastructure issue...');
    fireEvent.change(input, { target: { value: 'System is slow' } });
    expect(input).toHaveValue('System is slow');

    const sendButton = screen.getByRole('button', { name: 'Send message' });
    expect(sendButton).not.toBeDisabled();

    // Fire submit on form directly to ensure handler is called
    const form = screen.getByTestId('chat-form');
    fireEvent.submit(form);

    expect(await screen.findByText(/System is slow/)).toBeInTheDocument();
    expect(await screen.findByText(/Checking system/)).toBeInTheDocument();

    // Supervisor appears in message header and thinking process
    const supervisors = await screen.findAllByText(/Supervisor/);
    expect(supervisors.length).toBeGreaterThan(0);

    expect(globalThis.fetch).toHaveBeenCalledWith('/chat', expect.objectContaining({
      method: 'POST',
      body: expect.stringContaining('System is slow')
    }));
  });

  it('displays tool calls and thinking process', async () => {
    const streamData = [
      JSON.stringify({ type: 'activity', agent: 'Topology_Specialist' }) + '\n',
      JSON.stringify({ type: 'tool_call', tool: 'scan_infrastructure', args: {} }) + '\n',
      JSON.stringify({ type: 'message', content: 'Scanning complete.', agent: 'Topology_Specialist' }) + '\n',
      JSON.stringify({ type: 'final' }) + '\n'
    ];

    (globalThis.fetch as any).mockResolvedValueOnce(createStreamResponse(streamData));

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('Describe the infrastructure issue...');
    fireEvent.change(input, { target: { value: 'Scan infra' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() => {
        // Thinking process should be visible (mocked via activity/tool_call)
        // We can check for text that appears there.
        expect(screen.getByText(/Topology_Specialist/)).toBeInTheDocument();
        // Tool call visualization might be tricky to query by text depending on implementation
        // But message should be there
        expect(screen.getByText('Scanning complete.')).toBeInTheDocument();
    });
  });

  it('handles approval request', async () => {
    const streamData = [
      JSON.stringify({ type: 'approval_required' }) + '\n'
    ];

    (globalThis.fetch as any).mockResolvedValueOnce(createStreamResponse(streamData));

    render(<ChatInterface />);

    const input = screen.getByPlaceholderText('Describe the infrastructure issue...');
    fireEvent.change(input, { target: { value: 'Restart service' } });
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }));

    await waitFor(() => {
      expect(screen.getByText('Authorization Required: Execute Runbook?')).toBeInTheDocument();
      expect(screen.getByText('Approve')).toBeInTheDocument();
      expect(screen.getByText('Deny')).toBeInTheDocument();
    });

    // Test Approve
    const resumeStreamData = [
        JSON.stringify({ type: 'message', content: 'Service restarted.', agent: 'Automation_Specialist' }) + '\n',
        JSON.stringify({ type: 'final' }) + '\n'
    ];
    (globalThis.fetch as any).mockResolvedValueOnce(createStreamResponse(resumeStreamData));

    fireEvent.click(screen.getByText('Approve'));

    await waitFor(() => {
        expect(globalThis.fetch).toHaveBeenCalledWith('/chat/resume', expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('"action":"approve"')
        }));
        expect(screen.getByText('Service restarted.')).toBeInTheDocument();
    });
  });
});
