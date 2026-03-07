import { ConfigProvider, Layout } from 'antd'
import { BrowserRouter } from 'react-router-dom'
import AdminRoutes from './routes'
import zhCN from 'antd/locale/zh_CN'
import './App.css'

const { Content } = Layout

function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Layout style={{ minHeight: '100vh' }}>
          <Content>
            <AdminRoutes />
          </Content>
        </Layout>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App