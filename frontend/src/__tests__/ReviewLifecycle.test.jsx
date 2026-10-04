import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { ListingDetail } from '../pages/ListingDetail';
import { ReviewReport } from '../pages/ReviewReport';
import api from '../api/client';
import * as ToastContextModule from '../context/ToastContext';

describe('Review Lifecycle & Stale Results Management', () => {
  const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.spyOn(ToastContextModule, 'useToast').mockReturnValue(mockToast);
  });

  it('Scenario G: ListingDetail displays review history with distinct review records and timestamps', async () => {
    const mockListing = {
      id: 5,
      title: 'Mahaveer Herbal Infusion Tea',
      description: 'Herbal infusion tea crafted with natural ingredients.',
      category: 'Health & Personal Care',
      price: 24.99,
      currency: 'INR',
      listing_type: 'Product',
      seller: 'Mahaveer Naturals',
      status: 'revisions_pending',
      attributes: {},
      tags: [],
      reviews: [
        {
          id: 102,
          status: 'completed',
          summary: 'Latest review: Found 1 formatting issue.',
          overall_status: 'needs_review',
          findings: [{ id: 1 }],
          created_at: '2026-10-03T18:00:00Z',
        },
        {
          id: 101,
          status: 'completed',
          summary: 'First review: Found 2 health claims.',
          overall_status: 'flagged',
          findings: [{ id: 2 }, { id: 3 }],
          created_at: '2026-10-03T17:00:00Z',
        },
      ],
    };

    vi.spyOn(api, 'get').mockResolvedValue({ data: mockListing });

    render(
      <BrowserRouter>
        <ListingDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Mahaveer Herbal Infusion Tea')).toBeDefined();
    });

    // Both reviews are displayed in Review History with their distinct IDs
    expect(screen.getByText('Review #102')).toBeDefined();
    expect(screen.getByText('Review #101')).toBeDefined();
    expect(screen.getByText('Review History (2)')).toBeDefined();
  });

  it('Scenario J: Loading state resets after failed review attempt and displays actionable error banner', async () => {
    const mockListing = {
      id: 5,
      title: 'Mahaveer Herbal Infusion Tea',
      description: 'Herbal infusion tea crafted with natural ingredients.',
      category: 'Health & Personal Care',
      price: 24.99,
      currency: 'INR',
      listing_type: 'Product',
      seller: 'Mahaveer Naturals',
      status: 'draft',
      attributes: {},
      tags: [],
      reviews: [],
    };

    vi.spyOn(api, 'get').mockResolvedValue({ data: mockListing });
    vi.spyOn(api, 'post').mockRejectedValue(
      new Error('Gemini API is temporarily experiencing high demand (503 UNAVAILABLE) after 4 attempts.')
    );

    render(
      <BrowserRouter>
        <ListingDetail />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Run AI Review')).toBeDefined();
    });

    const runBtn = screen.getByText('Run AI Review');
    fireEvent.click(runBtn);

    // Wait for failure
    await waitFor(() => {
      expect(mockToast.error).toHaveBeenCalledWith(
        expect.stringContaining('503 UNAVAILABLE')
      );
    });

    // Error banner is displayed with actual error and "Try Again" button
    expect(screen.getByText('AI Review Attempt Failed:')).toBeDefined();
    expect(screen.getByText(/503 UNAVAILABLE/)).toBeDefined();
    expect(screen.getByText('Try Again')).toBeDefined();

    // Loading state is completely reset and button is not disabled
    const buttonAfterError = screen.getByRole('button', { name: /Run AI Review/i });
    expect(buttonAfterError.hasAttribute('disabled')).toBe(false);
  });
});
