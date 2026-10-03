import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { StatusBadge } from '../components/StatusBadge';

describe('StatusBadge Component', () => {
  it('renders Approved status properly', () => {
    render(<StatusBadge status="approved" />);
    expect(screen.getByText('Approved')).toBeDefined();
  });

  it('renders Revisions Pending status properly', () => {
    render(<StatusBadge status="revisions_pending" />);
    expect(screen.getByText('Revisions Pending')).toBeDefined();
  });

  it('renders Flagged status properly', () => {
    render(<StatusBadge status="flagged" />);
    expect(screen.getByText('Flagged')).toBeDefined();
  });
});
