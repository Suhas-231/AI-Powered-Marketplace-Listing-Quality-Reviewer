import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { SeverityBadge } from '../components/SeverityBadge';

describe('SeverityBadge Component', () => {
  it('renders High Severity badge with proper red styling', () => {
    const { container } = render(<SeverityBadge severity="High" />);
    expect(screen.getByText(/High Severity/i)).toBeDefined();
    expect(container.firstChild.className).toContain('bg-rose-100');
    expect(container.firstChild.className).toContain('text-rose-800');
  });

  it('renders Medium Severity badge with amber styling', () => {
    const { container } = render(<SeverityBadge severity="Medium" />);
    expect(screen.getByText(/Medium Severity/i)).toBeDefined();
    expect(container.firstChild.className).toContain('bg-amber-100');
    expect(container.firstChild.className).toContain('text-amber-800');
  });

  it('renders Low Severity badge with blue/neutral styling', () => {
    const { container } = render(<SeverityBadge severity="Low" />);
    expect(screen.getByText(/Low Severity/i)).toBeDefined();
    expect(container.firstChild.className).toContain('bg-sky-100');
    expect(container.firstChild.className).toContain('text-sky-800');
  });
});
