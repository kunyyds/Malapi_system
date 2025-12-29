import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import AppHeader from './components/Layout/AppHeader';
import MatrixPageSimple from './pages/MatrixPageSimple';
import FunctionDetailPage from './pages/FunctionDetailPage';
import SearchPage from './pages/SearchPage';
import AnalysisPage from './pages/AnalysisPage';
import TechniqueDetailPage from './pages/TechniqueDetailPage';
import './App.css';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <Layout className="app-layout">
      <AppHeader />
      <Content className="app-content">
        <Routes>
          <Route path="/" element={<MatrixPageSimple />} />
          <Route path="/matrix" element={<MatrixPageSimple />} />
          <Route path="/function/:id" element={<FunctionDetailPage />} />
          <Route path="/technique/:techniqueId" element={<TechniqueDetailPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/analysis" element={<AnalysisPage />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default App;