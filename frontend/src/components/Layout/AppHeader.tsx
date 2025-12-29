import React from 'react';
import { Layout, Menu, Typography, Space } from 'antd';
import {
  HomeOutlined,
  SearchOutlined,
  ExperimentOutlined,
  ApiOutlined,
  GithubOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import './AppHeader.css';

const { Header } = Layout;
const { Title } = Typography;

const AppHeader: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'ATT&CK矩阵',
    },
    {
      key: '/search',
      icon: <SearchOutlined />,
      label: '搜索',
    },
    {
      key: '/analysis',
      icon: <ExperimentOutlined />,
      label: 'AI分析',
    },
  ];

  const handleMenuClick = (e: any) => {
    navigate(e.key);
  };

  return (
    <Header className="app-header">
      <div className="header-left">
        <Title level={3} className="app-title" onClick={() => navigate('/')}>
          <Space>
            <ApiOutlined />
            MalAPI System
          </Space>
        </Title>
      </div>

      <div className="header-center">
        <Menu
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="header-menu"
        />
      </div>

      <div className="header-right">
        <Space>
          <a
            href="https://github.com/your-repo/malapi-system"
            target="_blank"
            rel="noopener noreferrer"
            className="github-link"
          >
            <GithubOutlined />
          </a>
        </Space>
      </div>
    </Header>
  );
};

export default AppHeader;