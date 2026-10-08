import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ChatPage from './pages/ChatPage'
import SearchPage from './pages/SearchPage'
import GovernmentServicesPage from './pages/GovernmentServicesPage'
import GovernmentOfficesPage from './pages/GovernmentOfficesPage'
import KnowledgeSourcesPage from './pages/KnowledgeSourcesPage'
import OfficialDocumentsPage from './pages/OfficialDocumentsPage'
import VerifiedSourcesPage from './pages/VerifiedSourcesPage'
import ConversationsPage from './pages/ConversationsPage'
import SearchHistoryPage from './pages/SearchHistoryPage'
import DatasetStatusPage from './pages/DatasetStatusPage'
import PipelineStatusPage from './pages/PipelineStatusPage'
import CommercializationPage from './pages/CommercializationPage'
import PageLayout from './components/layout/PageLayout'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><PageLayout /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="chat" element={<ChatPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="services" element={<GovernmentServicesPage />} />
            <Route path="government-services" element={<GovernmentServicesPage />} />
            <Route path="offices" element={<GovernmentOfficesPage />} />
            <Route path="government-offices" element={<GovernmentOfficesPage />} />
            <Route path="sources" element={<KnowledgeSourcesPage />} />
            <Route path="knowledge-sources" element={<KnowledgeSourcesPage />} />
            <Route path="documents" element={<OfficialDocumentsPage />} />
            <Route path="official-documents" element={<OfficialDocumentsPage />} />
            <Route path="verified" element={<VerifiedSourcesPage />} />
            <Route path="verified-sources" element={<VerifiedSourcesPage />} />
            <Route path="conversations" element={<ConversationsPage />} />
            <Route path="history" element={<SearchHistoryPage />} />
            <Route path="search-history" element={<SearchHistoryPage />} />
            <Route path="dataset" element={<DatasetStatusPage />} />
            <Route path="dataset-status" element={<DatasetStatusPage />} />
            <Route path="pipeline" element={<PipelineStatusPage />} />
            <Route path="pipeline-status" element={<PipelineStatusPage />} />
            <Route path="commercialization" element={<CommercializationPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
