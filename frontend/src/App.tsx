import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import Layout from './components/Layout';
import ProjectsPage from './pages/ProjectsPage';
import DashboardPage from './pages/DashboardPage';
import DashboardEditorPage from './pages/DashboardEditorPage';
import DatasetsPage from './pages/DatasetsPage';
import UploadPage from './pages/UploadPage';
import VisualBuilderPage from './pages/VisualBuilderPage';
import CalculationsPage from './pages/CalculationsPage';
import AnalyticsDashboardPage from './pages/AnalyticsDashboardPage';
import QueryHistoryPage from './pages/QueryHistoryPage';
import './App.css';

function App() {
  return (
    <ProjectProvider>
      <BrowserRouter>
        <Routes>
          {/* Analytics Dashboard - Full page layout (no sidebar) */}
          <Route path="/analytics" element={<AnalyticsDashboardPage />} />
          <Route path="/analytics/:reportId" element={<AnalyticsDashboardPage />} />
          
          {/* Main App with sidebar layout */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/projects" replace />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="upload" element={<UploadPage />} />
            <Route path="visual-builder" element={<VisualBuilderPage />} />
            <Route path="calculations" element={<CalculationsPage />} />
            <Route path="query-history" element={<QueryHistoryPage />} />
            <Route path="dashboards" element={<DashboardPage />} />
            <Route path="dashboards/new" element={<DashboardEditorPage />} />
            <Route path="dashboards/:id" element={<DashboardEditorPage />} />
            <Route path="dashboards/:id/edit" element={<DashboardEditorPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ProjectProvider>
  );
}

export default App;
