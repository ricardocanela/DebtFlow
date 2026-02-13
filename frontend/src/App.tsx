import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';

// Lazy-loaded pages — only loaded when navigated to
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage })),
);
const WorklistPage = lazy(() =>
  import('@/pages/WorklistPage').then((m) => ({ default: m.WorklistPage })),
);
const AccountsPage = lazy(() =>
  import('@/pages/AccountsPage').then((m) => ({ default: m.AccountsPage })),
);
const AccountDetailPage = lazy(() =>
  import('@/pages/AccountDetailPage').then((m) => ({ default: m.AccountDetailPage })),
);
const PaymentsPage = lazy(() =>
  import('@/pages/PaymentsPage').then((m) => ({ default: m.PaymentsPage })),
);
const ImportsPage = lazy(() =>
  import('@/pages/ImportsPage').then((m) => ({ default: m.ImportsPage })),
);
const ImportDetailPage = lazy(() =>
  import('@/pages/ImportDetailPage').then((m) => ({ default: m.ImportDetailPage })),
);
const SettingsPage = lazy(() =>
  import('@/pages/SettingsPage').then((m) => ({ default: m.SettingsPage })),
);

function PageLoader() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', padding: 48 }}>
      <Spin size="large" />
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route
            path="/"
            element={
              <RoleGuard
                roles={['agency_admin', 'superuser']}
                fallback={<Navigate to="/worklist" />}
              >
                <Suspense fallback={<PageLoader />}>
                  <DashboardPage />
                </Suspense>
              </RoleGuard>
            }
          />
          <Route
            path="/worklist"
            element={
              <Suspense fallback={<PageLoader />}>
                <WorklistPage />
              </Suspense>
            }
          />
          <Route
            path="/accounts"
            element={
              <RoleGuard roles={['agency_admin', 'superuser']}>
                <Suspense fallback={<PageLoader />}>
                  <AccountsPage />
                </Suspense>
              </RoleGuard>
            }
          />
          <Route
            path="/accounts/:id"
            element={
              <Suspense fallback={<PageLoader />}>
                <AccountDetailPage />
              </Suspense>
            }
          />
          <Route
            path="/payments"
            element={
              <Suspense fallback={<PageLoader />}>
                <PaymentsPage />
              </Suspense>
            }
          />
          <Route
            path="/imports"
            element={
              <RoleGuard roles={['agency_admin', 'superuser']}>
                <Suspense fallback={<PageLoader />}>
                  <ImportsPage />
                </Suspense>
              </RoleGuard>
            }
          />
          <Route
            path="/imports/:id"
            element={
              <RoleGuard roles={['agency_admin', 'superuser']}>
                <Suspense fallback={<PageLoader />}>
                  <ImportDetailPage />
                </Suspense>
              </RoleGuard>
            }
          />
          <Route
            path="/settings"
            element={
              <RoleGuard roles={['agency_admin', 'superuser']}>
                <Suspense fallback={<PageLoader />}>
                  <SettingsPage />
                </Suspense>
              </RoleGuard>
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
