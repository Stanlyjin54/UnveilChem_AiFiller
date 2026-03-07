import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '../contexts/AuthContext'
import AdminLayout from '../components/AdminLayout'
import Login from '../pages/Login'
import Dashboard from '../pages/Dashboard'
import UserManagement from '../pages/UserManagement'
import DocumentManagement from '../pages/DocumentManagement'
import AnalysisManagement from '../pages/AnalysisManagement'
import SystemSettings from '../pages/SystemSettings'
import ProtectedRoute from '../components/ProtectedRoute'

const AdminRoutes: React.FC = () => {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={
          <ProtectedRoute>
            <AdminLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="users" element={<UserManagement />} />
          <Route path="documents" element={<DocumentManagement />} />
          <Route path="analyses" element={<AnalysisManagement />} />
          <Route path="settings" element={<SystemSettings />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default AdminRoutes