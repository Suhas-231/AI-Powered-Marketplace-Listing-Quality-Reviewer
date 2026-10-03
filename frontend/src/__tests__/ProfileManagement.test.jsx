import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { ProfileModal } from '../components/ProfileModal';
import * as UserContextModule from '../context/UserContext';
import * as ToastContextModule from '../context/ToastContext';

describe('ProfileModal Component', () => {
  const mockUser = {
    id: 1,
    name: 'Suhas (Compliance Officer)',
    email: 'compliance@marketplace.local',
    role: 'Senior Reviewer',
    created_at: '2026-10-03T08:53:51',
  };

  const mockUpdateProfile = vi.fn().mockResolvedValue({ success: true, user: mockUser });
  const mockToast = { success: vi.fn(), error: vi.fn() };

  vi.spyOn(UserContextModule, 'useUser').mockReturnValue({
    user: mockUser,
    updateProfile: mockUpdateProfile,
  });

  vi.spyOn(ToastContextModule, 'useToast').mockReturnValue(mockToast);

  it('renders View Profile details correctly from database user object', () => {
    render(<ProfileModal isOpen={true} onClose={() => {}} initialMode="view" />);

    expect(screen.getAllByText('Suhas (Compliance Officer)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('compliance@marketplace.local').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Senior Reviewer').length).toBeGreaterThan(0);
    expect(screen.getAllByText(/#1/).length).toBeGreaterThan(0);
  });

  it('switches to Edit Profile mode and displays prepopulated form', () => {
    render(<ProfileModal isOpen={true} onClose={() => {}} initialMode="view" />);

    const editBtn = screen.getByText('Edit Profile');
    fireEvent.click(editBtn);

    expect(screen.getByText('Edit User Profile')).toBeDefined();
    const nameInput = screen.getByDisplayValue('Suhas (Compliance Officer)');
    const emailInput = screen.getByDisplayValue('compliance@marketplace.local');
    expect(nameInput).toBeDefined();
    expect(emailInput).toBeDefined();
  });

  it('shows validation errors when fields are cleared in Edit mode', () => {
    render(<ProfileModal isOpen={true} onClose={() => {}} initialMode="edit" />);

    const nameInput = screen.getByDisplayValue('Suhas (Compliance Officer)');
    fireEvent.change(nameInput, { target: { value: '' } });

    const saveBtn = screen.getByText('Save Changes');
    fireEvent.click(saveBtn);

    expect(screen.getByText('Full name is required.')).toBeDefined();
    expect(mockUpdateProfile).not.toHaveBeenCalled();
  });
});
