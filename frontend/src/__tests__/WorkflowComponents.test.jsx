import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { EmptyState } from '../components/EmptyState';
import { LoadingSkeleton } from '../components/LoadingSkeleton';

describe('UI Feedback & Workflow Components', () => {
  it('renders EmptyState with custom title, message and CTA button', () => {
    let clicked = false;
    render(
      <EmptyState
        title="No Listings Found"
        description="Please create your first listing to begin."
        actionText="Add New Item"
        onAction={() => { clicked = true; }}
      />
    );

    expect(screen.getByText('No Listings Found')).toBeDefined();
    expect(screen.getByText('Please create your first listing to begin.')).toBeDefined();
    const btn = screen.getByText('Add New Item');
    expect(btn).toBeDefined();
    btn.click();
    expect(clicked).toBe(true);
  });

  it('renders LoadingSkeleton placeholders without crashing', () => {
    const { container } = render(<LoadingSkeleton count={3} />);
    expect(container.getElementsByClassName('animate-pulse').length).toBeGreaterThan(0);
  });
});
