// import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { AuthProvider } from './contexts/AuthContext'
import Layout from './components/Layout'
import Login from './pages/Login.tsx'
import Register from './pages/Register.tsx'
import Dashboard from './pages/Dashboard.tsx'
import DocumentAnalyzer from './pages/DocumentAnalyzer.tsx'
import ImageAnalyzer from './pages/ImageAnalyzer.tsx'
import AdminPanel from './pages/AdminPanel.tsx'
import AutomationDashboard from './pages/AutomationDashboard.tsx'
import AutomationExecution from './pages/AutomationExecution'
import ParameterMapping from './pages/ParameterMapping'
import Profile from './pages/Profile.tsx'
import Settings from './pages/Settings.tsx'
import AgentPanel from './pages/AgentPanel.tsx'
import TranslationPanel from './pages/TranslationPanel.tsx'
import ReportPanel from './pages/ReportPanel.tsx'
import LLMConfigPage from './pages/LLMConfigPage.tsx'
import './App.css'

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="documents" element={<DocumentAnalyzer />} />
            <Route path="images" element={<ImageAnalyzer />} />
            <Route path="automation" element={<AutomationDashboard />} />
            <Route path="automation-execution" element={<AutomationExecution />} />
            <Route path="parameter-mapping" element={<ParameterMapping />} />
            <Route path="admin" element={<AdminPanel />} />
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
            <Route path="agent" element={<AgentPanel />} />
            <Route path="translation" element={<TranslationPanel />} />
            <Route path="report" element={<ReportPanel />} />
            <Route path="llm-config" element={<LLMConfigPage />} />
          </Route>
          </Routes>
        </Router>
      </AuthProvider>
    </ConfigProvider>
  )
}

export default App