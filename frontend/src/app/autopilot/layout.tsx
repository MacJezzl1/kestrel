import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Kestrel Autopilot — Autonomous Execution',
  description: 'Autonomous trading execution engine with risk controls, circuit breakers, and performance monitoring.',
};

export default function AutopilotLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
