import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  AutoComplete,
  Select,
  Button,
  Row,
  Col,
  Tag,
  Spin,
  Pagination,
  Empty,
  Rate
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { debounce } from '../utils/helpers';
import { searchApi, functionsApi } from '../services/api';
import { SearchResult, SearchSuggestion, AttCKTechnique } from '../types';
import './SearchPage.css';

const { Search } = Input;
const { Option } = Select;

const SearchPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchType, setSearchType] = useState<'all' | 'function' | 'code' | 'technique'>('all');
  const [techniqueFilter, setTechniqueFilter] = useState<string>('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [techniques, setTechniques] = useState<AttCKTechnique[]>([]);
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);

  // 加载技术列表
  const loadTechniques = async () => {
    try {
      const techniquesList = await functionsApi.getTechniquesList();
      setTechniques(techniquesList);
    } catch (error) {
      console.error('加载技术列表失败:', error);
    }
  };

  // 执行搜索
  const performSearch = async (query: string, page: number = 1) => {
    if (!query.trim()) return;

    try {
      setLoading(true);

      const response = await searchApi.searchFunctions({
        q: query.trim(),
        search_type: searchType,
        technique_filter: techniqueFilter || undefined,
        page,
        page_size: pageSize
      });

      setSearchResults(response.results);
      setTotal(response.total);
      setCurrentPage(response.page);

    } catch (error: any) {
      console.error('搜索失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取搜索建议
  const fetchSuggestions = async (query: string) => {
    if (!query.trim()) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await searchApi.getSearchSuggestions(query);
      setSuggestions(response.suggestions);
    } catch (error) {
      console.error('获取搜索建议失败:', error);
    }
  };

  // 防抖的搜索建议获取
  const debouncedFetchSuggestions = debounce(fetchSuggestions, 300);

  // 处理搜索
  const handleSearch = (value: string) => {
    setSearchQuery(value);
    if (value.trim()) {
      setCurrentPage(1);
      performSearch(value, 1);
    }
  };

  // 处理分页
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    performSearch(searchQuery, page);
  };

  // 处理建议项点击
  const handleSuggestionSelect = (value: string) => {
    setSearchQuery(value);
    setCurrentPage(1);
    performSearch(value, 1);
  };

  // 处理函数点击
  const handleFunctionClick = (functionId: number) => {
    navigate(`/function/${functionId}`);
  };

  // 重置搜索
  const handleReset = () => {
    setSearchQuery('');
    setSearchResults([]);
    setTotal(0);
    setCurrentPage(1);
    setTechniqueFilter('');
  };

  useEffect(() => {
    loadTechniques();
  }, []);

  return (
    <div className="search-page">
      <div className="page-container">
        <div className="page-header">
          <h1 className="page-title">搜索恶意软件API</h1>
          <p className="page-description">
            支持函数名、代码内容、ATT&CK技术的全文搜索
          </p>
        </div>

        {/* 搜索框 */}
        <Card className="search-card">
          <Row gutter={[16, 16]} align="middle">
            <Col xs={24} md={12}>
              <AutoComplete
                style={{ width: '100%' }}
                options={suggestions.map(s => ({
                  value: s.value,
                  label: (
                    <div className="suggestion-item">
                      <Tag color={s.type === 'function' ? 'blue' : 'orange'}>
                        {s.type === 'function' ? '函数' : '技术'}
                      </Tag>
                      {s.value}
                    </div>
                  )
                }))}
                onSelect={handleSuggestionSelect}
                onSearch={debouncedFetchSuggestions}
              >
                <Search
                  placeholder="输入关键词搜索..."
                  enterButton={<SearchOutlined />}
                  size="large"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onSearch={handleSearch}
                  loading={loading}
                />
              </AutoComplete>
            </Col>

            <Col xs={24} md={6}>
              <Select
                style={{ width: '100%' }}
                placeholder="搜索类型"
                value={searchType}
                onChange={setSearchType}
                size="large"
              >
                <Option value="all">全部</Option>
                <Option value="function">函数</Option>
                <Option value="code">代码</Option>
                <Option value="technique">ATT&CK技术</Option>
              </Select>
            </Col>

            <Col xs={24} md={6}>
              <Select
                style={{ width: '100%' }}
                placeholder="技术筛选"
                value={techniqueFilter}
                onChange={setTechniqueFilter}
                size="large"
                allowClear
                showSearch
                filterOption={(input, option) =>
                  String(option?.children || '').toLowerCase().includes(input.toLowerCase())
                }
              >
                {techniques.map(tech => (
                  <Option key={tech.technique_id} value={tech.technique_id}>
                    {tech.technique_id}: {tech.technique_name}
                  </Option>
                ))}
              </Select>
            </Col>
          </Row>

          <div className="search-actions">
            <Button
              icon={<ReloadOutlined />}
              onClick={handleReset}
              disabled={!searchQuery}
            >
              重置
            </Button>
          </div>
        </Card>

        {/* 搜索结果 */}
        <div className="search-results">
          {loading ? (
            <div className="search-loading">
              <Spin size="large" />
              <p>正在搜索...</p>
            </div>
          ) : searchResults.length > 0 ? (
            <>
              <div className="results-header">
                <h3>搜索结果 ({total} 条)</h3>
                <p>关键词: "{searchQuery}" | 类型: {searchType}</p>
              </div>

              <div className="results-list">
                {searchResults.map((result) => (
                  <Card
                    key={result.id}
                    className="result-card"
                    hoverable
                    onClick={() => handleFunctionClick(result.id)}
                  >
                    <div className="result-content">
                      <div className="result-header">
                        <h3>{result.alias}</h3>
                        <div className="result-meta">
                          <Rate
                            disabled
                            count={5}
                            value={result.relevance_score * 5}
                            style={{ fontSize: 14 }}
                          />
                          <Tag color="blue">{result.status}</Tag>
                        </div>
                      </div>

                      {result.summary && (
                        <p className="result-summary">
                          {result.summary}
                        </p>
                      )}

                      {result.techniques.length > 0 && (
                        <div className="result-techniques">
                          {result.techniques.map((tech, index) => (
                            <Tag
                              key={index}
                              color="orange"
                              className="technique-tag"
                            >
                              {tech.technique_id}
                            </Tag>
                          ))}
                        </div>
                      )}

                      <div className="result-footer">
                        <span className="hash-id">{result.hash_id}</span>
                        <span className="create-time">
                          {new Date(result.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* 分页 */}
              {total > pageSize && (
                <div className="pagination-container">
                  <Pagination
                    current={currentPage}
                    total={total}
                    pageSize={pageSize}
                    onChange={handlePageChange}
                    showSizeChanger={false}
                    showQuickJumper
                    showTotal={(total, range) =>
                      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
                    }
                  />
                </div>
              )}
            </>
          ) : searchQuery ? (
            <Empty
              description="没有找到相关结果"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ) : (
            <div className="search-placeholder">
              <div className="placeholder-content">
                <SearchOutlined style={{ fontSize: 64, color: '#d9d9d9' }} />
                <h3>开始搜索</h3>
                <p>输入关键词来搜索恶意软件API函数</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchPage;