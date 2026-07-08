import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from '@/components/layout/AppLayout'
import GenerateCommentary from '@/pages/GenerateCommentary'
import ReviewApproval from '@/pages/ReviewApproval'
import WorkflowPage from '@/pages/WorkflowPage'
import ArchitecturePage from '@/pages/ArchitecturePage'
import DemoFlowPage from '@/pages/DemoFlowPage'
import SettingsPage from '@/pages/SettingsPage'
import ClientsPage from '@/pages/ClientsPage'
import PortfolioDetail from '@/pages/PortfolioDetail'
import ReviewQueue from '@/pages/ReviewQueue'

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/clients" replace />} />
        <Route path="clients" element={<ClientsPage />} />
        <Route path="clients/:clientId" element={<ClientsPage />} />
        <Route path="portfolios/:mandateId" element={<PortfolioDetail />} />
        <Route path="generate" element={<GenerateCommentary />} />
        <Route path="queue" element={<ReviewQueue />} />
        <Route path="review/:id" element={<ReviewApproval />} />
        <Route path="review" element={<ReviewApproval />} />
        <Route path="workflow" element={<WorkflowPage />} />
        <Route path="architecture" element={<ArchitecturePage />} />
        <Route path="demo" element={<DemoFlowPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  )
}
