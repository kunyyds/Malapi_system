import React, { useState } from 'react';
import { Card, Button, Tag, Tooltip } from 'antd';
import {
  CopyOutlined,
  DownloadOutlined,
  FullscreenOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import message from 'antd/lib/message';
import './CodeViewer.css';

interface CodeViewerProps {
  code: string;
  language?: string;
  title?: string;
  showLineNumbers?: boolean;
  maxHeight?: number;
}

const CodeViewer: React.FC<CodeViewerProps> = ({
  code,
  language = 'cpp',
  title,
  showLineNumbers = true,
  maxHeight = 600
}) => {
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      message.success('代码已复制到剪贴板');
    } catch (error) {
      message.error('复制失败');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = title || `code.${language}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('文件下载已开始');
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // react-syntax-highlighter自带行号功能
  const processedCode = code;

  return (
    <div className={`code-viewer ${isFullscreen ? 'fullscreen' : ''}`}>
      <Card
        className="code-viewer-card"
        title={
          <div className="code-viewer-header">
            <div className="code-title">
              <FileTextOutlined />
              <span>{title || `源代码 (${language.toUpperCase()})`}</span>
            </div>
            <div className="code-actions">
              <Tooltip title="复制代码">
                <Button
                  type="text"
                  size="small"
                  icon={<CopyOutlined />}
                  onClick={handleCopy}
                />
              </Tooltip>
              <Tooltip title="下载文件">
                <Button
                  type="text"
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={handleDownload}
                />
              </Tooltip>
              <Tooltip title={isFullscreen ? '退出全屏' : '全屏显示'}>
                <Button
                  type="text"
                  size="small"
                  icon={<FullscreenOutlined />}
                  onClick={toggleFullscreen}
                />
              </Tooltip>
            </div>
          </div>
        }
        bodyStyle={{ padding: 0 }}
      >
        <div
          className="code-container"
          style={{ maxHeight: isFullscreen ? '100vh' : maxHeight }}
        >
          <div className="code-content">
            <SyntaxHighlighter
              language={language}
              style={vscDarkPlus}
              showLineNumbers={showLineNumbers}
              wrapLines={true}
              customStyle={{
                margin: 0,
                borderRadius: 0,
                fontSize: '14px',
                background: '#1e1e1e'
              }}
            >
              {processedCode}
            </SyntaxHighlighter>
          </div>
        </div>

        {/* 代码统计信息 */}
        <div className="code-stats">
          <Tag color="blue">语言: {language.toUpperCase()}</Tag>
          <Tag color="green">行数: {code.split('\n').length}</Tag>
          <Tag color="orange">字符数: {code.length}</Tag>
        </div>
      </Card>

      {/* 全屏遮罩 */}
      {isFullscreen && (
        <div className="fullscreen-overlay" onClick={toggleFullscreen}>
          <div className="fullscreen-content" onClick={(e) => e.stopPropagation()}>
            <Card
              title={
                <div className="code-viewer-header">
                  <div className="code-title">
                    <FileTextOutlined />
                    <span>{title || `源代码 (${language.toUpperCase()})`}</span>
                  </div>
                  <div className="code-actions">
                    <Button
                      type="text"
                      size="small"
                      icon={<FullscreenOutlined />}
                      onClick={toggleFullscreen}
                    >
                      退出全屏
                    </Button>
                  </div>
                </div>
              }
              bodyStyle={{ padding: 0 }}
            >
              <div className="code-container">
                <div className="code-content">
                  <SyntaxHighlighter
                    language={language}
                    style={vscDarkPlus}
                    showLineNumbers={showLineNumbers}
                    wrapLines={true}
                    customStyle={{
                      margin: 0,
                      borderRadius: 0,
                      fontSize: '14px',
                      background: '#1e1e1e'
                    }}
                  >
                    {processedCode}
                  </SyntaxHighlighter>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default CodeViewer;