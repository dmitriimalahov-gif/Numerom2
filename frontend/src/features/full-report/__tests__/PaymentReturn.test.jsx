import React, { act } from 'react';
import { createRoot } from 'react-dom/client';
global.TextEncoder = require('util').TextEncoder;
const { MemoryRouter, Routes, Route, useLocation } = require('react-router-dom');
const Success = require('../../../components/PaymentSuccess').default;
const Cancelled = require('../../../components/PaymentCancelled').default;
const { api } = require('../../../services/api');
jest.mock('../../../services/api', () => ({ api: { request: jest.fn() } }));
jest.mock('../../../components/AuthContext', () => ({ useAuth: () => ({ user: { id: 'owner' } }) }));
function Destination() { const location = useLocation(); return <p>{location.pathname}{location.search}</p>; }
let root, host;
beforeEach(() => { global.IS_REACT_ACT_ENVIRONMENT = true; api.request.mockReset(); host = document.createElement('div'); document.body.appendChild(host); root = createRoot(host); });
afterEach(async () => { await act(async () => root.unmount()); host.remove(); });
test.each(['/payment-success', '/payment-cancelled'])('%s routes this service to its report, not credit top-up', async path => {
  await act(async () => root.render(<MemoryRouter initialEntries={[`${path}?service=full-report&order_id=${'a'.repeat(64)}`]}><Routes><Route path="/payment-success" element={<Success />} /><Route path="/payment-cancelled" element={<Cancelled />} /><Route path="/dashboard/full-report" element={<Destination />} /></Routes></MemoryRouter>));
  expect(host.textContent).toBe(`/dashboard/full-report?order_id=${'a'.repeat(64)}`); expect(api.request).not.toHaveBeenCalled();
});
